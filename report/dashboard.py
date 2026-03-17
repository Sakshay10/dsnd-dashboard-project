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
you will use for subclassing
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

        # Set label
        label = model.name.capitalize()

        # Get options
        data = model.names()

        # Build dropdown manually
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

        return H1(f"{model.name.capitalize()} Performance")


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

        df.plot(ax=ax)

        self.set_axis_styling(ax, bordercolor="black", fontcolor="black")

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

        ax.barh([""], [pred])
        ax.set_xlim(0, 1)
        ax.set_title("Predicted Recruitment Risk", fontsize=20)

        self.set_axis_styling(ax, bordercolor="black", fontcolor="black")

        return fig


# Create a subclass of combined_components/CombinedComponent
# called Visualizations
class Visualizations(CombinedComponent):

    children = [
        LineChart(),
        BarChart()
    ]

    outer_div_type = Div(cls="grid")


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

        # ✅ MANUAL RADIO (bulletproof)
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

        self.children = [
            Header(),
            DashboardFilters(model),  
            Visualizations(),
            NotesTable()
        ]

        return super().call_children(entity_id, model)


# Initialize a fasthtml app
app = FastHTML()


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


@app.get("/team/{id}")
def team_view(id: str, r):

    profile_type = r.query_params.get("profile_type", "Team")

    return report(int(id), Team())


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