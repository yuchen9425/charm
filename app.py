from shiny import App, ui, render, reactive
import requests
import json
import urllib3

# Suppress SSL warnings globally (only if using verify=False is intentional in dev)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
            Shiny.setInputValue(k, params.get(k) || "");
          });
        } else {
          setTimeout(send, 300);
        }
      }

      send();
    })();
    """),

    # -------------------------------------------------
    # CSS
    # -------------------------------------------------

    ui.tags.style("""

    /* =========================================
       Global
    ========================================= */

    html, body {
        height: 100%;
        /* Removed overflow:hidden — prevents content clipping on small screens */
    }

    body {
        background: #f4f7fb;
        font-family: 'Segoe UI', sans-serif;
        color: #1f2937;
        padding: 10px 18px;
    }

    h1,h2,h3,h4,h5 {
        font-weight: 700;
    }

    /* =========================================
       Sidebar
    ========================================= */

    .sidebar {
        background: white;
        border-radius: 20px;
        padding: 18px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 8px 24px rgba(0,0,0,0.05);
    }

    /* =========================================
       Card
    ========================================= */

    .card {
        background: white;
        border-radius: 22px;
        padding: 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.05);
        border: 1px solid #eef2f7;
    }

    /* =========================================
       Section title
    ========================================= */

    .section-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 16px;
        color: #111827;
    }

    /* =========================================
       Summary Cards
    ========================================= */

    .summary-card {
        background: white;
        border-radius: 18px;
        padding: 16px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.04);
        border: 1px solid #eef2f7;
        text-align: center;
    }

    .summary-title {
        font-size: 14px;
        color: #6b7280;
        margin-bottom: 8px;
    }

    .summary-value {
        font-size: 34px;
        font-weight: 800;
        color: #111827;
    }

    /* =========================================
       Risk Number
    ========================================= */

    .risk-number {
        font-size: 64px;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 12px;
    }

    .risk-low  { color: #16a34a; }
    .risk-mid  { color: #f59e0b; }
    .risk-high { color: #dc2626; }

    /* =========================================
       Risk Tag
    ========================================= */

    .risk-tag {
        display: inline-block;
        padding: 7px 16px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 13px;
        margin-bottom: 16px;
    }

    .tag-low  { background: #dcfce7; color: #166534; }
    .tag-mid  { background: #fef3c7; color: #92400e; }
    .tag-high { background: #fee2e2; color: #991b1b; }

    /* =========================================
       Risk Bar
    ========================================= */

    .risk-bar {
        height: 14px;
        border-radius: 999px;
        background: linear-gradient(to right, #22c55e, #facc15, #ef4444);
        position: relative;
        margin-top: 12px;
    }

    .risk-marker {
        position: absolute;
        top: -5px;
        width: 4px;
        height: 24px;
        border-radius: 999px;
        background: #111827;
    }

    /* =========================================
       Factors
    ========================================= */

    .factor-item {
        background: #f9fafb;
        border-radius: 12px;
        padding: 10px 14px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 10px;
        border: 1px solid #e5e7eb;
    }

    .factor-yes { color: #16a34a; font-weight: 800; }
    .factor-no  { color: #dc2626; font-weight: 800; }

    /* =========================================
       Radio Buttons
    ========================================= */

    .shiny-input-radiogroup        { margin-bottom: 18px; }
    .shiny-input-radiogroup label  { font-weight: 700; font-size: 14px; }
    .form-check                    { margin-top: 6px; }

    /* =========================================
       JSON Viewer
    ========================================= */

    pre {
        background: #111827;
        color: #e5e7eb;
        border-radius: 14px;
        padding: 14px;
        max-height: 220px;
        overflow-y: auto;
        font-size: 12px;
    }

    /* =========================================
       Link
    ========================================= */

    a {
        text-decoration: none;
        color: #2563eb;
        font-weight: 600;
    }

    /* =========================================
       Hidden Inputs
    ========================================= */

    #token, #pid, #fhir, #obs {
        display: none !important;
    }

    """),

    # -------------------------------------------------
    # Hidden Inputs
    # -------------------------------------------------

    ui.input_text("token", ""),
    ui.input_text("pid",   ""),
    ui.input_text("fhir",  ""),
    ui.input_text("obs",   ""),

    # -------------------------------------------------
    # Title
    # -------------------------------------------------

    ui.h1(
        "Predict In-hospital Mortality by CHARM Score",
        style="margin-bottom:10px; font-weight:800; font-size:42px;"
    ),

    # -------------------------------------------------
    # FHIR Expandable
    # -------------------------------------------------

    ui.tags.details(
        ui.tags.summary("FHIR Patient & Observation Data"),
        ui.tags.pre(ui.output_text("patient_info"))
    ),

    # -------------------------------------------------
    # Main Layout
    # -------------------------------------------------

    ui.layout_sidebar(

        # FIX: sidebar_width belongs inside ui.sidebar(), not layout_sidebar()
        ui.sidebar(

            ui.div("Patient Clinical Features", class_="section-title"),

            ui.p(
                "Auto-populated from FHIR resources and editable by clinicians.",
                style="color:#6b7280; font-size:14px; margin-bottom:18px;"
            ),

            ui.input_radio_buttons(
                "chills", "Absence of Chills",
                {"No": "No", "Yes": "Yes"}, inline=True
            ),

            ui.input_radio_buttons(
                "hypothermia", "Hypothermia (Temp < 36°C)",
                {"No": "No", "Yes": "Yes"}, inline=True
            ),

            ui.input_radio_buttons(
                "anemia", "Anemia (RBC < 4M/uL)",
                {"No": "No", "Yes": "Yes"}, inline=True
            ),

            ui.input_radio_buttons(
                "rdw", "RDW > 14.5%",
                {"No": "No", "Yes": "Yes"}, inline=True
            ),

            ui.input_radio_buttons(
                "malignancy", "History of Malignancy",
                {"No": "No", "Yes": "Yes"}, inline=True
            ),

            width="280px",  # FIX: width goes here, inside ui.sidebar()
        ),

        # =============================================
        # Main Content
        # =============================================

        ui.div(

            ui.layout_columns(

                ui.div(
                    {"class": "summary-card"},
                    ui.div("CHARM Score",      class_="summary-title"),
                    ui.div(ui.output_text("score_text"), class_="summary-value")
                ),

                ui.div(
                    {"class": "summary-card"},
                    ui.div("Activated Factors", class_="summary-title"),
                    ui.div(ui.output_text("factor_count"), class_="summary-value")
                ),

                col_widths=[6, 6]
            ),

            ui.layout_columns(

                # Risk Card
                ui.div(
                    {"class": "card"},
                    ui.div("Estimated In-hospital Mortality Risk", class_="section-title"),
                    ui.output_ui("prob"),
                    ui.output_ui("risk_label"),
                    ui.output_ui("risk_bar"),
                    ui.hr(),
                    ui.p(ui.a(
                        "View Reference Paper",
                        href="https://www.ncbi.nlm.nih.gov/pubmed/?term=27832977",
                        target="_blank"
                    )),
                    ui.p("Produced by Dr. Chin-Chieh Wu",
                         style="color:#6b7280; font-size:13px; margin-bottom:4px;"),
                    ui.p("SMART on FHIR UI enhanced by Howard",
                         style="color:#6b7280; font-size:13px;")
                ),

                # Factors Card
                ui.div(
                    {"class": "card"},
                    ui.div("Contributing Clinical Factors", class_="section-title"),
                    ui.output_ui("factor_list")
                ),

                col_widths=[7, 5]
            )
        )
    )
)

# =====================================================
# CHARM Table
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

    # -------------------------------------------------
    # Fetch FHIR Data
    # -------------------------------------------------

    @reactive.Calc
    def fhir_data():

        if not (input.token() and input.pid() and input.fhir()):
            return {}

        headers = {
            "Authorization": f"Bearer {input.token()}",
            "Accept": "application/fhir+json"
        }

        data = {}

        try:
            data["patient"] = requests.get(
                f"{input.fhir()}/Patient/{input.pid()}",
                headers=headers,
                verify=False,
                timeout=10      # FIX: added timeout to prevent hanging
            ).json()
        except Exception as e:
            data["error_patient"] = str(e)

        if input.obs():
            try:
                data["observation"] = requests.get(
                    input.obs(),
                    headers=headers,
                    verify=False,
                    timeout=10  # FIX: added timeout
                ).json()
            except Exception as e:
                data["error_observation"] = str(e)

        return data

    # -------------------------------------------------
    # Display JSON
    # -------------------------------------------------

    @output
    @render.text
    def patient_info():
        return json.dumps(fhir_data(), indent=2, ensure_ascii=False)

    # -------------------------------------------------
    # Init UI from FHIR
    # -------------------------------------------------

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

            code = (
                c.get("code", {})
                 .get("coding", [{}])[0]
                 .get("code")
            )

            if code == "chills" and c.get("valueInteger") == 1:
                defaults["chills"] = "Yes"

            elif code == "malignancy" and c.get("valueInteger") == 1:
                defaults["malignancy"] = "Yes"

            elif code == "789-8" and \
                    c.get("valueQuantity", {}).get("value", 9) < 4:
                defaults["anemia"] = "Yes"

            elif code == "788-0" and \
                    c.get("valueQuantity", {}).get("value", 0) > 14.5:
                defaults["rdw"] = "Yes"

            elif code == "8310-5" and \
                    c.get("valueQuantity", {}).get("value", 99) < 36:
                defaults["hypothermia"] = "Yes"

        # FIX: use ui.update_*() instead of deprecated session.send_input_message()
        ui.update_radio_buttons(session, "chills",       selected=defaults["chills"])
        ui.update_radio_buttons(session, "hypothermia",  selected=defaults["hypothermia"])
        ui.update_radio_buttons(session, "anemia",       selected=defaults["anemia"])
        ui.update_radio_buttons(session, "rdw",          selected=defaults["rdw"])
        ui.update_radio_buttons(session, "malignancy",   selected=defaults["malignancy"])

    # -------------------------------------------------
    # Score  (FIX: wrapped in @reactive.Calc for proper dependency tracking)
    # -------------------------------------------------

    @reactive.Calc
    def score():
        return sum([
            input.chills()     == "Yes",
            input.hypothermia()== "Yes",
            input.anemia()     == "Yes",
            input.rdw()        == "Yes",
            input.malignancy() == "Yes",
        ])

    # -------------------------------------------------
    # Summary
    # -------------------------------------------------

    @output
    @render.text
    def score_text():
        return str(score())

    @output
    @render.text
    def factor_count():
        return f"{score()} / 5"

    # -------------------------------------------------
    # Risk Number
    # -------------------------------------------------

    @output
    @render.ui
    def prob():
        p   = CHARM_TABLE.get(score(), 0)
        cls = "risk-low" if p < 5 else "risk-mid" if p < 20 else "risk-high"
        return ui.div(f"{p:.2f} %", class_=f"risk-number {cls}")

    # -------------------------------------------------
    # Risk Label
    # -------------------------------------------------

    @output
    @render.ui
    def risk_label():
        p = CHARM_TABLE.get(score(), 0)
        if p < 5:
            return ui.div("Very Low Risk",  class_="risk-tag tag-low")
        elif p < 20:
            return ui.div("Moderate Risk",  class_="risk-tag tag-mid")
        else:
            return ui.div("High Risk",      class_="risk-tag tag-high")

    # -------------------------------------------------
    # Risk Bar
    # -------------------------------------------------

    @output
    @render.ui
    def risk_bar():
        p    = CHARM_TABLE.get(score(), 0)
        left = min(p / 40 * 100, 100)
        return ui.div(
            {"class": "risk-bar"},
            ui.div({"class": "risk-marker", "style": f"left:{left}%"})
        )

    # -------------------------------------------------
    # Clinical Factors
    # -------------------------------------------------

    @output
    @render.ui
    def factor_list():

        def row(label, val):
            active = val == "Yes"
            return ui.div(
                {"class": "factor-item"},
                ui.span("✔" if active else "✘",
                        class_="factor-yes" if active else "factor-no"),
                ui.div(label)
            )

        return ui.div(
            row("Absence of Chills",       input.chills()),
            row("Hypothermia (Temp < 36°C)", input.hypothermia()),
            row("Anemia (RBC < 4M/uL)",    input.anemia()),
            row("RDW > 14.5%",             input.rdw()),
            row("History of Malignancy",   input.malignancy()),
        )

# =====================================================
# App
# =====================================================

app = App(app_ui, server)
