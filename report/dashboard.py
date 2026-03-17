from fasthtml.common import *
import matplotlib.pyplot as plt

# Import QueryBase, Employee, Team from employee_events
from employee_events.query_base import QueryBase
from employee_events.employee import Employee
from employee_events.team import Team

# import the load_model function from the utils.py file
from utils import load_model

"""
Below, we import the parent classes
we will use for subclassing
"""
from base_components import (
    Dropdown,
    BaseComponent,
    Radio,
    MatplotlibViz,
    DataTable
)

from combined_components import FormGroup, CombinedComponent


# Create a subclass of base_components/dropdown
# called `ReportDropdown`
class ReportDropdown(Dropdown):

    def build_component(self, entity_id, model):

        # Setting label
        label = model.name.capitalize()

        # Get options
        data = model.names()

        # Building dropdown manually
        options = []

        for text, value in data:
            if value == entity_id:
                options.append(Option(text, value=value, selected=True))
            else:
                options.append(Option(text, value=value))

        return Div(
            Label(label),
            Select(
                *options,
                name=self.name,
                id=self.id
            )
        )

# Create a subclass of base_components/BaseComponent
# called `Header`
class Header(BaseComponent):

    def build_component(self, entity_id, model):

        title = (
            "Employee Performance"
            if model.name == "employee"
            else "Team Performance"
        )

        return H1(title)

# Create a subclass of base_components/MatplotlibViz
# called `LineChart`
class LineChart(MatplotlibViz):

    def visualization(self, entity_id, model):

        df = model.event_counts(entity_id)

        if df is None or df.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "No data available", ha='center')
            return fig

        df = df.fillna(0)

        df = df.set_index("event_date")

        df = df.sort_index()

        df = df.cumsum()

        df.columns = ["Positive", "Negative"]

        fig, ax = plt.subplots()

        df.plot(ax=ax, linewidth=2)
        ax.grid(True, linestyle="--", alpha=0.5)

        self.set_axis_styling(ax, bordercolor="white", fontcolor="white")

        ax.set_title("Event Counts Over Time", fontsize=20)
        ax.set_xlabel("Date")
        ax.set_ylabel("Events")

        return fig


# Create a subclass of base_components/MatplotlibViz
# called `BarChart`
class BarChart(MatplotlibViz):

    predictor = load_model()

    def visualization(self, entity_id, model):

        df = model.model_data(entity_id)

        if df is None or df.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "No data available", ha='center')
            return fig

        preds = self.predictor.predict_proba(df)

        preds = preds[:, 1]

        if model.name == "team":
            pred = preds.mean()
        else:
            pred = preds[0]

        fig, ax = plt.subplots()

        # Color logic
        if pred < 0.3:
            color = "green"
        elif pred < 0.7:
            color = "orange"
        else:
            color = "red"

        ax.barh(["Risk"], [pred], color=color)
        ax.set_xlim(0, 1)
        ax.set_title("Predicted Recruitment Risk", fontsize=20)

        self.set_axis_styling(ax, bordercolor="white", fontcolor="white")

        return fig


# Create a subclass of combined_components/CombinedComponent
# called Visualizations
class Visualizations(CombinedComponent):

    children = [
        LineChart(),
        BarChart()
    ]

    outer_div_type = Div(cls="charts")


# Create a subclass of base_components/DataTable
# called `NotesTable`
class NotesTable(DataTable):

    def component_data(self, entity_id, model):

        return model.notes(entity_id)


class DashboardFilters(FormGroup):

    id = "top-filters"
    action = "/update_data"
    method = "POST"

    def __init__(self, model):

        selected = model.name.capitalize()

        # manual radio button
        radio = Div(
            Label(
                Input(
                    type="radio",
                    name="profile_type",
                    value="Employee",
                    checked=(selected == "Employee"),
                    hx_get="/update_dropdown",
                    hx_target="#selector"
                ),
                " Employee"
            ),
            Label(
                Input(
                    type="radio",
                    name="profile_type",
                    value="Team",
                    checked=(selected == "Team"),
                    hx_get="/update_dropdown",
                    hx_target="#selector"
                ),
                " Team"
            )
        )

        self.children = [
            radio,
            ReportDropdown(
                id="selector",
                name="user-selection"
            )
        ]


# Create a subclass of CombinedComponents
# called `Report`
class Report(CombinedComponent):

    def call_children(self, entity_id, model):

        # define children properly
        self.children = [
            Header(),
            DashboardFilters(model),
            Visualizations(),
            NotesTable()
        ]

        # render children
        components = super().call_children(entity_id, model)

        # wrap layout
        return Div(
            H1("Employee Performance Dashboard", cls="title"),

            Div(components[1], cls="card filters"),   # filters
            Div(components[2], cls="card charts"),    # charts
            Div(components[3], cls="card table"),     # table

            cls="container"
        )

# Initialize a fasthtml app
app = FastHTML(
    hdrs=(Link(rel="stylesheet", href="/assets/report.css"),)
)


# Initialize the `Report` class
report = Report()


# Root route
@app.get("/")
def index():

    return report(1, Employee())


# Employee route
@app.get("/employee/{id}")
def employee_view(id: str, r):

    profile_type = r.query_params.get("profile_type", "Employee")

    return report(int(id), Employee())

# Team route
@app.get("/team/{id}")
def team_view(id: str, r):

    profile_type = r.query_params.get("profile_type", "Team")

    return report(int(id), Team())

from pathlib import Path
from fasthtml.common import Response

@app.get("/assets/report.css")
def serve_css():
    css_path = Path(__file__).resolve().parents[1] / "assets" / "report.css"
    
    with open(css_path, "r") as f:
        return Response(f.read(), media_type="text/css")


# Keep the below code unchanged!
@app.get('/update_dropdown{r}')
def update_dropdown(r):

    dropdown = ReportDropdown(id="selector", name="user-selection")

    if r.query_params['profile_type'] == 'Team':
        return dropdown(None, Team())

    elif r.query_params['profile_type'] == 'Employee':
        return dropdown(None, Employee())


@app.post('/update_data')
async def update_data(r):
    from fasthtml.common import RedirectResponse

    data = await r.form()

    profile_type = data._dict['profile_type']
    id = data._dict['user-selection']

    if profile_type == 'Employee':
        return RedirectResponse(f"/employee/{id}?profile_type=Employee", status_code=303)

    elif profile_type == 'Team':
        return RedirectResponse(f"/team/{id}?profile_type=Team", status_code=303)


serve()