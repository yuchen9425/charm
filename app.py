from shiny import App, ui, render, reactive
import requests
import json

# =====================================================
# UI
# =====================================================
app_ui = ui.page_fluid(

    # -------------------------------------------------
    # URL hash → Shiny input
    # -------------------------------------------------
    ui.tags.script("""
    (function () {
      const hash = window.location.hash.substring(1);
      const params = new URLSearchParams(hash);
      function send() {
        if (window.Shiny && Shiny.setInputValue) {
          ["token","pid","fhir","obs"].forEach(k=>{
            Shiny.setInputValue(k, params.get(k));
          });
        } else {
          setTimeout(send, 300);
        }
      }
      send();
    })();
    """),

    # -------------------------------------------------
    # CSS (dashboard style)
    # -------------------------------------------------
    ui.tags.style("""
    body { background:#f5f7fa; }

    .card {
      background:white;
      border-radius:12px;
      padding:20px;
      box-shadow:0 4px 12px rgba(0,0,0,.08);
      margin-bottom:20px;
    }

    .risk-number {
      font-size:48px;
      font-weight:700;
      line-height:1;
    }

    .risk-low  { color:#2e7d32; }
    .risk-mid  { color:#f9a825; }
    .risk-high { color:#c62828; }

    .risk-bar {
      height:12px;
      border-radius:6px;
      background:linear-gradient(to right,#c8e6c9,#fff59d,#ef9a9a);
      margin-top:12px;
      position:relative;
    }

    .risk-marker {
      position:absolute;
      top:-4px;
      width:2px;
      height:20px;
      background:black;
    }

    .factor-yes { color:#2e7d32; font-weight:600; }
    .factor-no  { color:#c62828; font-weight:600; }

    #token,#pid,#fhir,#obs { display:none !important; }
    """),

    # -------------------------------------------------
    # Hidden inputs (do not rename)
    # -------------------------------------------------
    ui.input_text("token",""),
    ui.input_text("pid",""),
    ui.input_text("fhir",""),
    ui.input_text("obs",""),

    ui.h2("Predict In-hospital Mortality by CHARM score in Patients with Suspected Sepsis"),

    ui.tags.details(
        ui.tags.summary("FHIR Patient & Observation Data (click to expand)"),
        ui.tags.pre(ui.output_text("patient_info"))
    ),

    ui.layout_sidebar(

        # ================= Sidebar =================
        ui.sidebar(
            ui.p("Please fill the below details (auto-populated from FHIR, editable)"),

            ui.input_radio_buttons("chills","noChills (absence of Chills)",
                                   {"No":"No","Yes":"Yes"},inline=True),

            ui.input_radio_buttons("hypothermia","Hypothermia (templo < 36 °C)",
                                   {"No":"No","Yes":"Yes"},inline=True),

            ui.input_radio_buttons("anemia","Anemia (RBC < 4M/uL)",
                                   {"No":"No","Yes":"Yes"},inline=True),

            ui.input_radio_buttons("rdw","RDW > 14.5%",
                                   {"No":"No","Yes":"Yes"},inline=True),

            ui.input_radio_buttons("malignancy","Malignancy (history)",
                                   {"No":"No","Yes":"Yes"},inline=True),
        ),

        # ================= Main =================
        ui.div(

            ui.div(
                {"class":"card"},
                ui.h4("Estimated In-hospital Mortality Risk (%)"),
                ui.output_ui("prob"),
                ui.output_ui("risk_label"),
                ui.output_ui("risk_bar"),
                ui.hr(),
                ui.help_text(
                    ui.a("Click here to see the reference",
                         href="https://www.ncbi.nlm.nih.gov/pubmed/?term=27832977")
                ),
                ui.help_text("Produced by Dr. Chin-Chieh Wu"),
                ui.help_text("UI enhance and implement in SMART on FHIR by Howard")
            ),

            ui.div(
                {"class":"card"},
                ui.h4("Contributing Clinical Factors"),
                ui.output_ui("factor_list")
            )
        )
    )
)

# =====================================================
# CHARM Table (unchanged)
# =====================================================
CHARM_TABLE = {
    0: 0.36,
    1: 1.89,
    2: 5.79,
    3: 12.97,
    4: 23.58,
    5: 34.15
}

# =====================================================
# Server
# =====================================================
def server(input, output, session):

    # ---------------- FHIR fetch ----------------
    @reactive.Calc
    def fhir_data():

        if not (input.token() and input.pid() and input.fhir()):
            return {}

        headers = {
            "Authorization": f"Bearer {input.token()}",
            "Accept": "application/fhir+json"
        }

        data = {}
        data["patient"] = requests.get(
            f"{input.fhir()}/Patient/{input.pid()}",
            headers=headers, verify=False
        ).json()

        if input.obs():
            data["observation"] = requests.get(
                input.obs(),
                headers=headers, verify=False
            ).json()

        return data

    @output
    @render.text
    def patient_info():
        return json.dumps(fhir_data(), indent=2)

    # ---------------- Init from Observation ----------------
    @reactive.Effect
    def init_ui_from_fhir():

        obs = fhir_data().get("observation")
        if not obs or "component" not in obs:
            return

        defaults = dict(
            chills="No",
            hypothermia="No",
            anemia="No",
            rdw="No",
            malignancy="No",
        )

        for c in obs["component"]:
            code = c.get("code",{}).get("coding",[{}])[0].get("code")

            if code=="chills" and c.get("valueInteger")==1:
                defaults["chills"]="Yes"
            elif code=="malignancy" and c.get("valueInteger")==1:
                defaults["malignancy"]="Yes"
            elif code=="789-8" and c.get("valueQuantity",{}).get("value",9)<4:
                defaults["anemia"]="Yes"
            elif code=="788-0" and c.get("valueQuantity",{}).get("value",0)>14.5:
                defaults["rdw"]="Yes"
            elif code=="8310-5" and c.get("valueQuantity",{}).get("value",99)<36:
                defaults["hypothermia"]="Yes"

        for k,v in defaults.items():
            session.send_input_message(k,{"value":v})

    # ---------------- Risk calc ----------------
    def score():
        return sum([
            input.chills()=="Yes",
            input.hypothermia()=="Yes",
            input.anemia()=="Yes",
            input.rdw()=="Yes",
            input.malignancy()=="Yes",
        ])

    @output
    @render.ui
    def prob():
        p = CHARM_TABLE.get(score(),0)
        cls = "risk-low" if p<5 else "risk-mid" if p<20 else "risk-high"
        return ui.div(f"{p:.2f} %",class_=f"risk-number {cls}")

    @output
    @render.ui
    def risk_label():
        p = CHARM_TABLE.get(score(),0)
        if p<5:
            return ui.span("● Very Low Risk",class_="risk-low")
        elif p<20:
            return ui.span("● Moderate Risk",class_="risk-mid")
        else:
            return ui.span("● High Risk",class_="risk-high")

    @output
    @render.ui
    def risk_bar():
        p = CHARM_TABLE.get(score(),0)
        left = min(p/40*100,100)
        return ui.div(
            {"class":"risk-bar"},
            ui.div({"class":"risk-marker","style":f"left:{left}%"}))

    @output
    @render.ui
    def factor_list():

        def row(label,val):
            ok = val=="Yes"
            return ui.div(
                ui.span("✔ " if ok else "✘ ",
                        class_="factor-yes" if ok else "factor-no"),
                ui.span(label)
            )

        return ui.div(
            row("No Chills",input.chills()),
            row("Hypothermia (templo<36°C)",input.hypothermia()),
            row("Anemia (RBC < 4M/µL)",input.anemia()),
            row("RDW > 14.5%",input.rdw()),
            row("History of malignancy",input.malignancy())
        )

# =====================================================
app = App(app_ui, server)
