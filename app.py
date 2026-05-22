from shiny import App, ui, render, reactive
import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app_ui = ui.page_fluid(

    ui.tags.script("""
    (function () {
      const hash = window.location.hash.substring(1);
      const params = new URLSearchParams(hash);
      function send() {
        if (window.Shiny && Shiny.setInputValue) {
          ["token","pid","fhir","obs"].forEach(k=>{
            Shiny.setInputValue(k, params.get(k) || "");
          });
        } else {
          setTimeout(send, 300);
        }
      }
      send();
    })();
    """),

    ui.tags.style("""
    html, body { height: 100%; }
    body {
        background: #f4f7fb;
        font-family: 'Segoe UI', sans-serif;
        color: #1f2937;
        padding: 12px 20px 20px;
        margin: 0;
    }
    .page-header {
        display: flex; align-items: baseline;
        justify-content: space-between; margin-bottom: 10px;
        flex-wrap: wrap; gap: 6px;
    }
    .page-title { font-size: 26px; font-weight: 800; color: #111827; }
    .page-meta  { font-size: 12px; color: #9ca3af; }
    details { margin-bottom: 10px; font-size: 13px; color: #6b7280; }
    details summary { cursor: pointer; user-select: none; }
    .sidebar {
        background: white; border-radius: 16px; padding: 16px 18px;
        border: 1px solid #e5e7eb; box-shadow: 0 4px 14px rgba(0,0,0,0.04);
    }
    .sidebar-title {
        font-size: 13px; font-weight: 700; letter-spacing:.04em;
        text-transform: uppercase; color: #9ca3af; margin-bottom: 4px;
    }
    .sidebar-sub { font-size: 12px; color: #9ca3af; margin-bottom: 14px; line-height: 1.4; }
    .shiny-input-radiogroup { margin-bottom: 12px; }
    .shiny-input-radiogroup > label {
        font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 3px; display: block;
    }
    .form-check { margin-top: 2px; }
    .summary-card {
        background: white; border-radius: 14px; padding: 14px 16px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.04); border: 1px solid #eef2f7; text-align: center;
    }
    .summary-title {
        font-size: 12px; font-weight: 600; letter-spacing:.04em;
        text-transform: uppercase; color: #9ca3af; margin-bottom: 6px;
    }
    .summary-value { font-size: 28px; font-weight: 800; color: #111827; line-height: 1; }
    .card {
        background: white; border-radius: 16px; padding: 18px 20px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.04); border: 1px solid #eef2f7;
    }
    .section-title {
        font-size: 13px; font-weight: 700; letter-spacing:.04em;
        text-transform: uppercase; color: #9ca3af; margin-bottom: 12px;
    }
    .risk-number { font-size: 52px; font-weight: 800; line-height: 1; margin-bottom: 8px; }
    .risk-low  { color: #16a34a; }
    .risk-mid  { color: #d97706; }
    .risk-high { color: #dc2626; }
    .risk-tag {
        display: inline-block; padding: 5px 14px; border-radius: 999px;
        font-weight: 700; font-size: 12px; margin-bottom: 14px;
    }
    .tag-low  { background: #dcfce7; color: #166534; }
    .tag-mid  { background: #fef3c7; color: #92400e; }
    .tag-high { background: #fee2e2; color: #991b1b; }
    .risk-bar {
        height: 10px; border-radius: 999px;
        background: linear-gradient(to right, #22c55e, #facc15, #ef4444);
        position: relative; margin-top: 10px; margin-bottom: 4px;
    }
    .risk-marker {
        position: absolute; top: -5px; width: 3px; height: 20px;
        border-radius: 999px; background: #1f2937;
    }
    .risk-bar-labels {
        display: flex; justify-content: space-between;
        font-size: 11px; color: #9ca3af; margin-bottom: 14px;
    }
    .factor-item {
        display: flex; align-items: center; gap: 10px; padding: 8px 10px;
        border-radius: 10px; margin-bottom: 6px; background: #f9fafb;
        border: 1px solid #e5e7eb; font-size: 13px;
    }
    .factor-yes { color: #16a34a; font-weight: 800; font-size: 15px; }
    .factor-no  { color: #dc2626; font-weight: 800; font-size: 15px; }
    hr { border: none; border-top: 1px solid #f3f4f6; margin: 14px 0 10px; }
    .footer-text { font-size: 12px; color: #9ca3af; margin-bottom: 2px; }
    a { text-decoration: none; color: #2563eb; font-weight: 600; font-size: 12px; }
    pre {
        background: #111827; color: #e5e7eb; border-radius: 10px;
        padding: 12px; max-height: 200px; overflow-y: auto; font-size: 11px;
    }
    #token, #pid, #fhir, #obs { display: none !important; }
    /* DEBUG banner */
    #debug-bar {
        background: #1e3a5f; color: #93c5fd; font-family: monospace;
        font-size: 12px; padding: 6px 12px; border-radius: 8px;
        margin-bottom: 10px;
    }
    """),

    ui.input_text("token", ""),
    ui.input_text("pid",   ""),
    ui.input_text("fhir",  ""),
    ui.input_text("obs",   ""),

    ui.div(
        ui.div("Predict In-hospital Mortality — CHARM Score", class_="page-title"),
        ui.div("SMART on FHIR · Sandbox", class_="page-meta"),
        class_="page-header"
    ),

    # DEBUG bar — shows live reactive values so we can confirm reactivity works
    ui.div(ui.output_text("debug_bar"), id="debug-bar"),

    ui.tags.details(
        ui.tags.summary("▸ FHIR Patient & Observation Data"),
        ui.tags.pre(ui.output_text("patient_info"))
    ),

    ui.layout_sidebar(

        ui.sidebar(
            ui.div("Clinical Features", class_="sidebar-title"),
            ui.p("Auto-populated from FHIR. Editable by clinicians.", class_="sidebar-sub"),
            ui.input_radio_buttons("chills",      "Absence of Chills",         {"No":"No","Yes":"Yes"}, inline=True),
            ui.input_radio_buttons("hypothermia", "Hypothermia (Temp < 36°C)", {"No":"No","Yes":"Yes"}, inline=True),
            ui.input_radio_buttons("anemia",      "Anemia (RBC < 4M/uL)",      {"No":"No","Yes":"Yes"}, inline=True),
            ui.input_radio_buttons("rdw",         "RDW > 14.5%",               {"No":"No","Yes":"Yes"}, inline=True),
            ui.input_radio_buttons("malignancy",  "History of Malignancy",     {"No":"No","Yes":"Yes"}, inline=True),
            width="240px",
        ),

        ui.layout_columns(

            ui.div(
                ui.div("CHARM Score",    class_="summary-title"),
                ui.div(ui.output_text("score_text"), class_="summary-value"),
                class_="summary-card"
            ),
            ui.div(
                ui.div("Mortality Risk", class_="summary-title"),
                ui.output_ui("prob_inline"),
                class_="summary-card"
            ),
            ui.div(
                ui.div("Active Factors", class_="summary-title"),
                ui.div(ui.output_text("factor_count"), class_="summary-value"),
                class_="summary-card"
            ),

            ui.div(
                ui.div("Estimated Mortality Risk", class_="section-title"),
                ui.output_ui("prob"),
                ui.output_ui("risk_label"),
                ui.output_ui("risk_bar"),
                ui.hr(),
                ui.p(ui.a("View Reference Paper",
                           href="https://www.ncbi.nlm.nih.gov/pubmed/?term=27832977",
                           target="_blank")),
                class_="card"
            ),

            ui.div(
                ui.div("Contributing Clinical Factors", class_="section-title"),
                ui.output_ui("factor_list"),
                class_="card"
            ),

            col_widths=[4, 4, 4, 6, 6],
            row_heights=["auto", "1fr"],
        ),
    )
)

CHARM_TABLE = {0:0.36, 1:1.89, 2:5.79, 3:12.97, 4:23.58, 5:34.15}

def server(input, output, session):

    @reactive.Calc
    def fhir_data():
        if not (input.token() and input.pid() and input.fhir()):
            return {}
        headers = {"Authorization": f"Bearer {input.token()}", "Accept": "application/fhir+json"}
        data = {}
        try:
            data["patient"] = requests.get(
                f"{input.fhir()}/Patient/{input.pid()}",
                headers=headers, verify=False, timeout=10).json()
        except Exception as e:
            data["error_patient"] = str(e)
        if input.obs():
            try:
                data["observation"] = requests.get(
                    input.obs(), headers=headers, verify=False, timeout=10).json()
            except Exception as e:
                data["error_observation"] = str(e)
        return data

    @output
    @render.text
    def patient_info():
        return json.dumps(fhir_data(), indent=2, ensure_ascii=False)

    @reactive.Effect
    def init_ui_from_fhir():
        obs = fhir_data().get("observation")
        if not obs or "component" not in obs:
            return
        defaults = dict(chills="No", hypothermia="No", anemia="No", rdw="No", malignancy="No")
        for c in obs["component"]:
            code = c.get("code", {}).get("coding", [{}])[0].get("code")
            if   code == "chills"     and c.get("valueInteger") == 1:                           defaults["chills"]      = "Yes"
            elif code == "malignancy" and c.get("valueInteger") == 1:                           defaults["malignancy"]  = "Yes"
            elif code == "789-8"      and c.get("valueQuantity", {}).get("value", 9)   < 4:    defaults["anemia"]      = "Yes"
            elif code == "788-0"      and c.get("valueQuantity", {}).get("value", 0)   > 14.5: defaults["rdw"]         = "Yes"
            elif code == "8310-5"     and c.get("valueQuantity", {}).get("value", 99) < 36:    defaults["hypothermia"] = "Yes"
        for k, v in defaults.items():
            session.send_input_message(
                k,
                {"value": v}
            )

    @reactive.Calc
    def score():
        s = sum([
            input.chills()      == "Yes",
            input.hypothermia() == "Yes",
            input.anemia()      == "Yes",
            input.rdw()         == "Yes",
            input.malignancy()  == "Yes",
        ])
        print(f"[DEBUG] score() = {s}  chills={input.chills()} hypo={input.hypothermia()}")
        return s

    # DEBUG output — placed OUTSIDE layout_sidebar to confirm basic reactivity
    @output
    @render.text
    def debug_bar():
        return (f"score={score()}  "
                f"chills={input.chills()}  hypo={input.hypothermia()}  "
                f"anemia={input.anemia()}  rdw={input.rdw()}  malig={input.malignancy()}")

    @output
    @render.text
    def score_text():
        return str(score())

    @output
    @render.text
    def factor_count():
        return f"{score()} / 5"

    @output
    @render.ui
    def prob_inline():
        p   = CHARM_TABLE.get(score(), 0)
        cls = "risk-low" if p < 5 else "risk-mid" if p < 20 else "risk-high"
        return ui.div(f"{p:.2f}%", class_=f"summary-value {cls}")

    @output
    @render.ui
    def prob():
        p   = CHARM_TABLE.get(score(), 0)
        cls = "risk-low" if p < 5 else "risk-mid" if p < 20 else "risk-high"
        return ui.div(f"{p:.2f} %", class_=f"risk-number {cls}")

    @output
    @render.ui
    def risk_label():
        p = CHARM_TABLE.get(score(), 0)
        if p < 5:    return ui.div("Very Low Risk", class_="risk-tag tag-low")
        elif p < 20: return ui.div("Moderate Risk", class_="risk-tag tag-mid")
        else:        return ui.div("High Risk",      class_="risk-tag tag-high")

    @output
    @render.ui
    def risk_bar():
        p    = CHARM_TABLE.get(score(), 0)
        left = min(p / 40 * 100, 100)
        return ui.div(
            ui.div({"class":"risk-bar"},
                   ui.div({"class":"risk-marker", "style":f"left:{left}%"})),
            ui.div(ui.span("0%"), ui.span("20%"), ui.span("40%+"),
                   class_="risk-bar-labels")
        )

    @output
    @render.ui
    def factor_list():
        def row(label, val):
            active = val == "Yes"
            return ui.div(
                {"class":"factor-item"},
                ui.span("✔" if active else "✘",
                        class_="factor-yes" if active else "factor-no"),
                ui.div(label)
            )
        return ui.div(
            row("Absence of Chills",         input.chills()),
            row("Hypothermia (Temp < 36°C)", input.hypothermia()),
            row("Anemia (RBC < 4M/uL)",      input.anemia()),
            row("RDW > 14.5%",               input.rdw()),
            row("History of Malignancy",     input.malignancy()),
        )

app = App(app_ui, server)
