from shiny import App, ui, render, reactive
import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =====================================================
# UI
# =====================================================

app_ui = ui.page_fluid(

    # =================================================
    # URL HASH → SHINY INPUT
    # =================================================

    ui.tags.script("""
    (function () {

      const hash = window.location.hash.substring(1);
      const params = new URLSearchParams(hash);

      function send() {

        if (window.Shiny && Shiny.setInputValue) {

          ["token","pid","fhir","obs"].forEach(k => {
            Shiny.setInputValue(k, params.get(k) || "");
          });

        } else {

          setTimeout(send, 300);
        }
      }

      send();

    })();
    """),

    # =================================================
    # CSS
    # =================================================

    ui.tags.style("""

    html, body {
        height: 100%;
        margin: 0;
    }

    body {
        background: #f4f7fb;
        font-family: 'Segoe UI', sans-serif;
        color: #1f2937;
        padding: 14px 22px;
    }

    /* =========================================
       Header
    ========================================= */

    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        margin-bottom: 12px;
    }

    .page-title {
        font-size: 34px;
        font-weight: 800;
        color: #111827;
    }

    .page-meta {
        font-size: 13px;
        color: #9ca3af;
    }

    /* =========================================
       Sidebar
    ========================================= */

    .sidebar {
        background: white;
        border-radius: 18px;
        padding: 18px;
        border: 1px solid #e5e7eb;

        box-shadow:
            0 6px 18px rgba(0,0,0,0.04);
    }

    .sidebar-title {

        font-size: 14px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .05em;

        color: #9ca3af;

        margin-bottom: 6px;
    }

    .sidebar-sub {

        font-size: 12px;
        color: #9ca3af;

        margin-bottom: 16px;

        line-height: 1.5;
    }

    .shiny-input-radiogroup {
        margin-bottom: 14px;
    }

    .shiny-input-radiogroup > label {

        font-size: 13px;
        font-weight: 700;

        color: #374151;
    }

    /* =========================================
       Cards
    ========================================= */

    .card {

        background: white;

        border-radius: 18px;

        padding: 18px;

        border: 1px solid #e5e7eb;

        box-shadow:
            0 6px 18px rgba(0,0,0,0.04);
    }

    .section-title {

        font-size: 13px;

        font-weight: 800;

        text-transform: uppercase;

        letter-spacing: .05em;

        color: #9ca3af;

        margin-bottom: 12px;
    }

    /* =========================================
       Summary Cards
    ========================================= */

    .summary-card {

        background: white;

        border-radius: 16px;

        padding: 14px;

        text-align: center;

        border: 1px solid #e5e7eb;

        box-shadow:
            0 4px 14px rgba(0,0,0,0.04);
    }

    .summary-title {

        font-size: 12px;

        font-weight: 700;

        text-transform: uppercase;

        letter-spacing: .05em;

        color: #9ca3af;

        margin-bottom: 6px;
    }

    .summary-value {

        font-size: 30px;

        font-weight: 800;

        line-height: 1;
    }

    /* =========================================
       Risk Colors
    ========================================= */

    .risk-low {
        color: #16a34a;
    }

    .risk-mid {
        color: #d97706;
    }

    .risk-high {
        color: #dc2626;
    }

    /* =========================================
       Gauge
    ========================================= */

    .gauge-container {

        display: flex;

        flex-direction: column;

        align-items: center;

        justify-content: center;
    }

    .gauge-circle {

        width: 240px;
        height: 120px;

        border-top-left-radius: 240px;
        border-top-right-radius: 240px;

        overflow: hidden;

        position: relative;

        background:
            linear-gradient(
                to right,
                #22c55e,
                #facc15,
                #ef4444
            );
    }

    .gauge-inner {

        position: absolute;

        top: 18px;
        left: 18px;

        width: 204px;
        height: 102px;

        background: white;

        border-top-left-radius: 204px;
        border-top-right-radius: 204px;
    }

    .gauge-needle {

        position: absolute;

        bottom: 0;
        left: 50%;

        width: 4px;
        height: 92px;

        background: #111827;

        border-radius: 999px;

        transform-origin: bottom center;
    }

    .gauge-value {

        font-size: 58px;

        font-weight: 800;

        margin-top: -8px;
    }

    /* =========================================
       Risk Tag
    ========================================= */

    .risk-tag {

        display: inline-block;

        padding: 6px 14px;

        border-radius: 999px;

        font-size: 13px;

        font-weight: 700;

        margin-top: 10px;
    }

    .tag-low {
        background: #dcfce7;
        color: #166534;
    }

    .tag-mid {
        background: #fef3c7;
        color: #92400e;
    }

    .tag-high {
        background: #fee2e2;
        color: #991b1b;
    }

    /* =========================================
       Interpretation
    ========================================= */

    .interpretation-box {

        background: #f9fafb;

        border-radius: 12px;

        padding: 14px;

        border: 1px solid #e5e7eb;

        font-size: 13px;

        line-height: 1.6;

        color: #374151;
    }

    /* =========================================
       Patient Card
    ========================================= */

    .patient-row {

        display: flex;

        justify-content: space-between;

        margin-bottom: 10px;

        font-size: 13px;
    }

    .patient-label {

        color: #6b7280;

        font-weight: 600;
    }

    .patient-value {

        color: #111827;

        font-weight: 700;
    }

    /* =========================================
       Factor Items
    ========================================= */

    .factor-item {

        display: flex;

        align-items: center;

        gap: 10px;

        padding: 10px 12px;

        margin-bottom: 8px;

        border-radius: 12px;

        background: #f9fafb;

        border: 1px solid #e5e7eb;

        font-size: 13px;
    }

    .factor-yes {

        color: #16a34a;

        font-size: 16px;

        font-weight: 800;
    }

    .factor-no {

        color: #dc2626;

        font-size: 16px;

        font-weight: 800;
    }

    /* =========================================
       JSON
    ========================================= */

    details {
        margin-bottom: 10px;
    }

    details summary {
        cursor: pointer;
        font-size: 13px;
        color: #6b7280;
    }

    pre {

        background: #111827;

        color: #e5e7eb;

        border-radius: 12px;

        padding: 12px;

        max-height: 220px;

        overflow-y: auto;

        font-size: 11px;
    }

    /* =========================================
       Hide Hidden Inputs
    ========================================= */

    #token, #pid, #fhir, #obs {
        display: none !important;
    }

    """),

    # =================================================
    # HIDDEN INPUTS
    # =================================================

    ui.input_text("token", ""),
    ui.input_text("pid", ""),
    ui.input_text("fhir", ""),
    ui.input_text("obs", ""),

    # =================================================
    # HEADER
    # =================================================

    ui.div(

        ui.div(
            "Predict In-hospital Mortality — CHARM Score",
            class_="page-title"
        ),

        ui.div(
            "SMART on FHIR Dashboard",
            class_="page-meta"
        ),

        class_="page-header"
    ),

    # =================================================
    # FHIR RAW DATA
    # =================================================

    ui.tags.details(

        ui.tags.summary(
            "FHIR Patient & Observation Data"
        ),

        ui.tags.pre(
            ui.output_text("patient_info")
        )
    ),

    # =================================================
    # MAIN LAYOUT
    # =================================================

    ui.layout_sidebar(

        # =============================================
        # SIDEBAR
        # =============================================

        ui.sidebar(

            ui.div(
                "Clinical Features",
                class_="sidebar-title"
            ),

            ui.p(
                "Auto-populated from FHIR. Editable by clinicians.",
                class_="sidebar-sub"
            ),

            ui.input_radio_buttons(
                "chills",
                "Absence of Chills",
                {"No":"No","Yes":"Yes"},
                inline=True
            ),

            ui.input_radio_buttons(
                "hypothermia",
                "Hypothermia (Temp < 36°C)",
                {"No":"No","Yes":"Yes"},
                inline=True
            ),

            ui.input_radio_buttons(
                "anemia",
                "Anemia (RBC < 4M/uL)",
                {"No":"No","Yes":"Yes"},
                inline=True
            ),

            ui.input_radio_buttons(
                "rdw",
                "RDW > 14.5%",
                {"No":"No","Yes":"Yes"},
                inline=True
            ),

            ui.input_radio_buttons(
                "malignancy",
                "History of Malignancy",
                {"No":"No","Yes":"Yes"},
                inline=True
            ),

            width="260px"
        ),

        # =============================================
        # MAIN CONTENT
        # =============================================

        ui.div(

            # =========================================
            # SUMMARY ROW
            # =========================================

            ui.layout_columns(

                ui.div(

                    ui.div(
                        "CHARM Score",
                        class_="summary-title"
                    ),

                    ui.div(
                        ui.output_text("score_text"),
                        class_="summary-value"
                    ),

                    class_="summary-card"
                ),

                ui.div(

                    ui.div(
                        "Mortality Risk",
                        class_="summary-title"
                    ),

                    ui.output_ui("prob_inline"),

                    class_="summary-card"
                ),

                ui.div(

                    ui.div(
                        "Active Factors",
                        class_="summary-title"
                    ),

                    ui.div(
                        ui.output_text("factor_count"),
                        class_="summary-value"
                    ),

                    class_="summary-card"
                ),

                col_widths=[4,4,4]
            ),

            ui.br(),

            # =========================================
            # SECOND ROW
            # =========================================

            ui.layout_columns(

                # =====================================
                # PATIENT OVERVIEW
                # =====================================

                ui.div(

                    {"class":"card"},

                    ui.div(
                        "Patient Overview",
                        class_="section-title"
                    ),

                    ui.output_ui("patient_summary")
                ),

                # =====================================
                # RISK CARD
                # =====================================

                ui.div(

                    {"class":"card"},

                    ui.div(
                        "Estimated Mortality Risk",
                        class_="section-title"
                    ),

                    ui.output_ui("gauge_ui"),

                    ui.output_ui("risk_label"),

                    ui.br(),

                    ui.div(
                        "Clinical Interpretation",
                        class_="section-title"
                    ),

                    ui.output_ui("interpretation")
                ),

                # =====================================
                # FACTOR CARD
                # =====================================

                ui.div(

                    {"class":"card"},

                    ui.div(
                        "Contributing Clinical Factors",
                        class_="section-title"
                    ),

                    ui.output_ui("factor_list")
                ),

                col_widths=[3,5,4]
            )
        )
    )
)

# =====================================================
# CHARM TABLE
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
# SERVER
# =====================================================

def server(input, output, session):

    # =============================================
    # FHIR DATA
    # =============================================

    @reactive.Calc
    def fhir_data():

        if not (
            input.token()
            and input.pid()
            and input.fhir()
        ):
            return {}

        headers = {
            "Authorization":
                f"Bearer {input.token()}",
            "Accept":
                "application/fhir+json"
        }

        data = {}

        try:

            data["patient"] = requests.get(
                f"{input.fhir()}/Patient/{input.pid()}",
                headers=headers,
                verify=False,
                timeout=10
            ).json()

        except Exception as e:

            data["error_patient"] = str(e)

        if input.obs():

            try:

                data["observation"] = requests.get(
                    input.obs(),
                    headers=headers,
                    verify=False,
                    timeout=10
                ).json()

            except Exception as e:

                data["error_observation"] = str(e)

        return data

    # =============================================
    # DISPLAY JSON
    # =============================================

    @output
    @render.text
    def patient_info():

        return json.dumps(
            fhir_data(),
            indent=2,
            ensure_ascii=False
        )

    # =============================================
    # INIT FROM FHIR
    # =============================================

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
            malignancy="No"
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

        for k, v in defaults.items():

            session.send_input_message(
                k,
                {"value": v}
            )

    # =============================================
    # SCORE
    # =============================================

    @reactive.Calc
    def score():

        return sum([

            input.chills() == "Yes",

            input.hypothermia() == "Yes",

            input.anemia() == "Yes",

            input.rdw() == "Yes",

            input.malignancy() == "Yes"
        ])

    # =============================================
    # SUMMARY OUTPUTS
    # =============================================

    @output
    @render.text
    def score_text():

        return str(score())

    @output
    @render.text
    def factor_count():

        return f"{score()} / 5"

    # =============================================
    # INLINE RISK
    # =============================================

    @output
    @render.ui
    def prob_inline():

        p = CHARM_TABLE.get(score(), 0)

        cls = (
            "risk-low"
            if p < 5 else
            "risk-mid"
            if p < 20 else
            "risk-high"
        )

        return ui.div(
            f"{p:.2f}%",
            class_=f"summary-value {cls}"
        )

    # =============================================
    # PATIENT SUMMARY
    # =============================================

    @output
    @render.ui
    def patient_summary():

        patient = fhir_data().get("patient", {})

        gender = patient.get("gender", "Unknown")

        birth = patient.get("birthDate", "Unknown")

        pid = patient.get("id", "Unknown")

        return ui.div(

            ui.div(

                ui.span(
                    "Patient ID",
                    class_="patient-label"
                ),

                ui.span(
                    pid,
                    class_="patient-value"
                ),

                class_="patient-row"
            ),

            ui.div(

                ui.span(
                    "Gender",
                    class_="patient-label"
                ),

                ui.span(
                    gender,
                    class_="patient-value"
                ),

                class_="patient-row"
            ),

            ui.div(

                ui.span(
                    "Birth Date",
                    class_="patient-label"
                ),

                ui.span(
                    birth,
                    class_="patient-value"
                ),

                class_="patient-row"
            )
        )

    # =============================================
    # GAUGE UI
    # =============================================

    @output
    @render.ui
    def gauge_ui():

        p = CHARM_TABLE.get(score(), 0)

        angle = min((p / 40) * 180 - 90, 90)

        cls = (
            "risk-low"
            if p < 5 else
            "risk-mid"
            if p < 20 else
            "risk-high"
        )

        return ui.div(

            {"class":"gauge-container"},

            ui.div(

                {"class":"gauge-circle"},

                ui.div({"class":"gauge-inner"}),

                ui.div(
                    {
                        "class":"gauge-needle",
                        "style":f"transform: rotate({angle}deg);"
                    }
                )
            ),

            ui.div(
                f"{p:.2f}%",
                class_=f"gauge-value {cls}"
            )
        )

    # =============================================
    # RISK LABEL
    # =============================================

    @output
    @render.ui
    def risk_label():

        p = CHARM_TABLE.get(score(), 0)

        if p < 5:

            return ui.div(
                "Very Low Risk",
                class_="risk-tag tag-low"
            )

        elif p < 20:

            return ui.div(
                "Moderate Risk",
                class_="risk-tag tag-mid"
            )

        else:

            return ui.div(
                "High Risk",
                class_="risk-tag tag-high"
            )

    # =============================================
    # INTERPRETATION
    # =============================================

    @output
    @render.ui
    def interpretation():

        active = []

        if input.hypothermia() == "Yes":
            active.append("hypothermia")

        if input.anemia() == "Yes":
            active.append("anemia")

        if input.rdw() == "Yes":
            active.append("elevated RDW")

        if input.malignancy() == "Yes":
            active.append("malignancy history")

        if input.chills() == "Yes":
            active.append("absence of chills")

        if len(active) == 0:

            text = (
                "This patient currently demonstrates "
                "very low predicted in-hospital mortality risk "
                "with no major CHARM risk factors identified."
            )

        else:

            factors = ", ".join(active)

            text = (
                f"This patient demonstrates elevated predicted "
                f"in-hospital mortality risk associated with "
                f"{factors}."
            )

        return ui.div(
            text,
            class_="interpretation-box"
        )

    # =============================================
    # FACTOR LIST
    # =============================================

    @output
    @render.ui
    def factor_list():

        def row(label, val):

            active = val == "Yes"

            return ui.div(

                {"class":"factor-item"},

                ui.span(
                    "✔" if active else "✘",
                    class_=
                        "factor-yes"
                        if active
                        else "factor-no"
                ),

                ui.div(label)
            )

        return ui.div(

            row(
                "Absence of Chills",
                input.chills()
            ),

            row(
                "Hypothermia (Temp < 36°C)",
                input.hypothermia()
            ),

            row(
                "Anemia (RBC < 4M/uL)",
                input.anemia()
            ),

            row(
                "RDW > 14.5%",
                input.rdw()
            ),

            row(
                "History of Malignancy",
                input.malignancy()
            )
        )

# =====================================================
# APP
# =====================================================

app = App(app_ui, server)
