import sys
import random
import logging
import datetime
import threading
import time

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLabel, QListWidget, QSpinBox, \
    QDoubleSpinBox, QDialog, QGridLayout, QLineEdit, QDialogButtonBox, QFileDialog, QWidget, QComboBox, QProgressBar, \
    QTextEdit
from PyQt5.QtGui import QIcon
import webbrowser

from plotly.subplots import make_subplots
from scipy.stats import gaussian_kde
import dash
from dash import dcc, html
import plotly.graph_objects as go
import numpy as np

import dash_bootstrap_components as dbc
from scipy import stats


class HarmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(400, 200)
        self.setWindowTitle('Add New Harm')

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QGridLayout(self)

        self.name = QLineEdit(self)
        self.type = QComboBox(self)
        self.type.addItems(["Operational Outage", "Availability Attack"])
        self.magnitude = QComboBox(self)
        self.magnitude.addItems(["Low", "Medium", "High"])
        self.cost_lower_bound = QDoubleSpinBox(self)
        self.cost_lower_bound.setRange(0.0, 999999999.99)
        self.cost_lower_bound.setSingleStep(10)
        self.cost_lower_bound.valueChanged.connect(self.updateMaxValue)
        self.cost_higher_bound = QDoubleSpinBox(self)
        self.cost_higher_bound.setRange(0.0, 999999999.99)
        self.cost_higher_bound.setSingleStep(10)
        self.cost_higher_bound.valueChanged.connect(self.updateMinValue)
        self.probability = QComboBox(self)
        self.probability.addItems(["Low", "Medium", "High"])

        self.layout.addWidget(QLabel("Name:"), 0, 0)
        self.layout.addWidget(self.name, 0, 1)
        self.layout.addWidget(QLabel("Type:"), 1, 0)
        self.layout.addWidget(self.type, 1, 1)
        self.layout.addWidget(QLabel("Magnitude:"), 2, 0)
        self.layout.addWidget(self.magnitude, 2, 1)
        self.layout.addWidget(QLabel("Cost (Min):"), 3, 0)
        self.layout.addWidget(self.cost_lower_bound, 3, 1)
        self.layout.addWidget(QLabel("Cost (Max):"), 4, 0)
        self.layout.addWidget(self.cost_higher_bound, 4, 1)
        self.layout.addWidget(QLabel("Probability:"), 5, 0)
        self.layout.addWidget(self.probability, 5, 1)
        self.layout.addWidget(self.buttonBox, 6, 0, 1, 2)

    def updateMaxValue(self, value):
        self.cost_higher_bound.setMinimum(value)

    def updateMinValue(self, value):
        self.cost_lower_bound.setMaximum(value)

    def getValues(self):
        return (self.name.text(), self.type.currentText(), self.magnitude.currentText(),
                self.cost_lower_bound.value(), self.cost_higher_bound.value(), self.probability.currentText())


class ThreatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(400, 200)
        self.setWindowTitle('Add New Threat')

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QGridLayout(self)

        self.name = QLineEdit(self)

        self.type = QComboBox(self)
        self.type.addItems(["Operational Outage", "Availability Attack"])

        self.case_count = QSpinBox(self)
        self.case_count.setRange(0, 999999999)
        self.case_count.setSingleStep(100)

        self.probability = QDoubleSpinBox(self)
        self.probability.setRange(0.0, 1.0)
        self.probability.setSingleStep(0.1)
        self.probability.setDecimals(4)

        self.interval_probability = QDoubleSpinBox(self)
        self.interval_probability.setRange(0.0, 1.0)
        self.interval_probability.setSingleStep(0.1)
        self.interval_probability.setDecimals(4)

        self.duration = QSpinBox(self)
        self.duration.setRange(0, 999999999)
        self.duration.setSingleStep(10)

        self.interval_count = QDoubleSpinBox(self)
        self.interval_count.setRange(0.0, 999999999.99)
        self.probability.setSingleStep(10.00)

        self.risk_level = QComboBox(self)
        self.risk_level.addItems(["Low", "Medium", "High"])

        self.layout.addWidget(QLabel("Name:"), 0, 0)
        self.layout.addWidget(self.name, 0, 1)
        self.layout.addWidget(QLabel("Type:"), 1, 0)
        self.layout.addWidget(self.type, 1, 1)
        self.layout.addWidget(QLabel("Case Count:"), 2, 0)
        self.layout.addWidget(self.case_count, 2, 1)
        self.layout.addWidget(QLabel("Probability:"), 3, 0)
        self.layout.addWidget(self.probability, 3, 1)
        self.layout.addWidget(QLabel("Interval Probability:"), 4, 0)
        self.layout.addWidget(self.interval_probability, 4, 1)
        self.layout.addWidget(QLabel("Duration:"), 5, 0)
        self.layout.addWidget(self.duration, 5, 1)
        self.layout.addWidget(QLabel("Interval Count:"), 6, 0)
        self.layout.addWidget(self.interval_count, 6, 1)
        self.layout.addWidget(QLabel("Risk Level:"), 7, 0)
        self.layout.addWidget(self.risk_level, 7, 1)
        self.layout.addWidget(self.buttonBox, 8, 0, 1, 2)

    def getValues(self):
        return self.name.text(), self.type.currentText(), self.case_count.value(), self.probability.value(), self.interval_probability.value(), self.duration.value(), self.interval_count.value(), self.risk_level.currentText()


class ControlDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(400, 200)
        self.setWindowTitle('Add New Control')

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QGridLayout(self)

        self.standard = QLineEdit(self)
        self.control_type = QComboBox(self)
        self.control_type.addItems(["Operational Outage", "Availability Attack"])
        self.value = QComboBox(self)
        self.value.addItems(["Low", "Medium", "High"])
        self.automated = QComboBox(self)
        self.automated.addItems(["Yes", "No"])
        self.overall_value = QComboBox(self)
        self.overall_value.addItems(["Low", "Medium", "High"])
        self.effectiveness = QDoubleSpinBox(self)
        self.effectiveness.setRange(0.0, 1.0)
        self.effectiveness.setSingleStep(0.1)

        self.layout.addWidget(QLabel("Standard:"), 0, 0)
        self.layout.addWidget(self.standard, 0, 1)
        self.layout.addWidget(QLabel("Type:"), 1, 0)
        self.layout.addWidget(self.control_type, 1, 1)
        self.layout.addWidget(QLabel("Value:"), 2, 0)
        self.layout.addWidget(self.value, 2, 1)
        self.layout.addWidget(QLabel("Automated:"), 3, 0)
        self.layout.addWidget(self.automated, 3, 1)
        self.layout.addWidget(QLabel("Overall Value:"), 4, 0)
        self.layout.addWidget(self.overall_value, 4, 1)
        self.layout.addWidget(QLabel("Effectiveness:"), 5, 0)
        self.layout.addWidget(self.effectiveness, 5, 1)
        self.layout.addWidget(self.buttonBox, 6, 0, 1, 2)

    def getValues(self):
        return self.standard.text(), self.control_type.currentText(), self.value.currentText(), self.automated.currentText(), self.overall_value.currentText(), self.effectiveness.value()



class EditThreatDialog(ThreatDialog):
    def __init__(self, name, type, case_count, probability, interval_probability, duration, interval_count, risk_level, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Edit Threat')
        self.resize(400, 200)
        self.name.setText(name)
        self.type.setCurrentText(type)
        self.case_count.setValue(case_count)
        self.probability.setValue(probability)
        self.interval_probability.setValue(interval_probability)
        self.duration.setValue(duration)
        self.interval_count.setValue(interval_count)
        self.risk_level.setCurrentText(risk_level)

    def getValues(self):
        return self.name.text(), self.type.currentText(), self.case_count.value(), self.probability.value(), self.interval_probability.value(), self.duration.value(), self.interval_count.value(), self.risk_level.currentText()



class EditHarmDialog(HarmDialog):
    def __init__(self, name, harm_type, magnitude, cost_lower_bound, cost_higher_bound, probability, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Edit Harm')
        self.resize(400, 200)
        self.name.setText(name)
        self.type.setCurrentText(harm_type)
        self.magnitude.setCurrentText(magnitude)
        self.cost_lower_bound.setValue(cost_lower_bound)
        self.cost_higher_bound.setValue(cost_higher_bound)
        self.probability.setCurrentText(probability)


class EditControlDialog(ControlDialog):
    def __init__(self, standard, control_type, value, automated, overall_value, effectiveness, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Edit Control')
        self.resize(400, 200)
        self.standard.setText(standard)
        self.control_type.setCurrentText(control_type)
        self.value.setCurrentText(value)
        self.automated.setCurrentText(automated)
        self.overall_value.setCurrentText(overall_value)
        self.effectiveness.setValue(effectiveness)


def create_loss_distribution_graph(losses_distribution):
    fig = go.Figure(data=[go.Histogram(x=losses_distribution, nbinsx=50, marker_color='red')])
    fig.update_layout(
        title="Impact Distribution",
        xaxis_title="Impact",
        yaxis_title="Frequency",
        bargap=0.1,
    )
    return fig.to_dict()


def create_cvar_estimates_graph(losses_distribution):
    kde = gaussian_kde(losses_distribution)
    x_kde = np.linspace(min(losses_distribution), max(losses_distribution), 100)
    y_kde = kde(x_kde)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Histogram(x=losses_distribution, nbinsx=50, name="Histogram", marker_color='red'),
                  secondary_y=False)
    # fig.add_trace(go.Scatter(x=x_kde, y=y_kde, mode='lines', name="KDE", line=dict(color='black')), secondary_y=True)

    percentile_95 = np.percentile(losses_distribution, 95)

    fig.add_shape(
        type="line",
        x0=percentile_95,
        x1=percentile_95,
        y0=0,
        y1=1,
        yref="paper",
        line={"color": "black", "width": 2},
    )

    fig.add_annotation(
        x=percentile_95,
        y=0.95,
        yref="paper",
        text="95th percentile",
        showarrow=True,
        arrowhead=1,
        ax=20,
        ay=-30,
    )

    # Calculate the 95th percentile CVaR (Expected Shortfall)
    cvar_95 = np.mean([loss for loss in losses_distribution if loss >= percentile_95])

    # Add CVaR (Expected Shortfall) as an annotation
    fig.add_annotation(
        x=percentile_95,
        y=0.85,
        yref="paper",
        text=f"VaR: {str(cvar_95)[:2]}M",
        showarrow=False,
        font={'color': "black"},
    )

    fig.update_layout(
        title="Cyber VaR",
        xaxis_title="Impact",
        yaxis_title="Frequency",
        bargap=0.1,
    )
    fig.update_yaxes(title_text="Density", secondary_y=True)

    return fig.to_dict()


def create_assign_losses_by_threat_graph(threat_losses_distribution):
    # Calculate total losses per threat
    threat_losses = {threat_id: sum(losses) for threat_id, losses in threat_losses_distribution.items()}

    # Modify keys for readability
    threat_losses = {"DDoS" if threat_id == "T1" else "Operational Incident" if threat_id == "T2" else threat_id: loss for
                     threat_id, loss in threat_losses.items()}

    # Create a bar chart
    fig = go.Figure(data=go.Bar(x=list(threat_losses.keys()), y=list(threat_losses.values()), marker_color='red'))
    fig.update_layout(title='Total Impact per Threat', xaxis_title='Threats', yaxis_title='Total Impact')

    return fig.to_dict()


def create_control_effectiveness_graph(unmitigated_losses, losses_distribution):
    slope, intercept, a, b, c = stats.linregress(unmitigated_losses, losses_distribution)
    line_x = np.linspace(min(unmitigated_losses), max(unmitigated_losses), 100)
    line_y = slope * line_x + intercept
    fig = go.Figure(data=go.Scatter(x=unmitigated_losses, y=losses_distribution, mode='markers', marker_color='red'))
    fig.add_trace(go.Scatter(x=line_x, y=line_y, mode='lines', line=dict(color='black')))
    fig.update_layout(title='Counterfactual Analysis', xaxis_title='Unmitigated ', yaxis_title='Mitigated ',
                      showlegend=False)

    return fig.to_dict()


def run_dash_server(losses_distribution, threat_losses_distribution, unmitigated_losses, static_fields,
                    static_field_names, incident_types, institutions):

    incident_list = []
    for incident in incident_types:
        incident_list.append(html.Li(incident))

    institution_list = []
    for institution in institutions:
        institution_list.append(html.Li(institution))

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = dbc.Container([
        # Title
        dbc.Row([
            dbc.Col(html.H1('Payment Systems Cyber Risk Centre', style={'textAlign': 'center', 'margin': '15px'}), width=12)
        ], className="mb-0"),
        # First row
        dbc.Row([
            # Static numbers
            dbc.Col([
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4(static_fields[0], className="card-title"),
                            html.P(static_field_names[0], className="card-text"),
                        ]
                    ), className="mb-2"
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4(static_fields[1], className="card-title"),
                            html.P(static_field_names[1], className="card-text"),
                        ]
                    ), className="mb-2"
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4(static_fields[2], className="card-title"),
                            html.P(static_field_names[2], className="card-text"),
                        ]
                    ), className="mb-2"
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4(static_fields[3], className="card-title"),
                            html.P(static_field_names[3], className="card-text"),
                        ]
                    ), className="mb-2"
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4(static_fields[4], className="card-title"),
                            html.P(static_field_names[4], className="card-text"),
                        ]
                    ), className="mb-2"
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4(static_fields[5], className="card-title"),
                            html.P(static_field_names[5], className="card-text"),
                        ]
                    )
                ),
            ], md=2),
            # Panel B and C
            dbc.Col([
                html.Div([
                    html.H4("Incident Types", style={'textAlign': 'center'}),
                    html.Ul(incident_list, style={'textAlign': 'center'})
                ], style={
                    'border': '2px solid',
                    'borderRadius': '5px',
                    'padding': '10px',
                    'marginBottom': '10px',
                    # 'width': '150px',
                    'height': '300px'
                }),
                html.Div([
                    html.H4("Incident Resources", style={'textAlign': 'center'}),
                    html.Ul(institution_list, style={'textAlign': 'center'})
                ], style={
                    'border': '2px solid',
                    'borderRadius': '5px',
                    'padding': '10px',
                    # 'width': '150px',
                    'height': '300px'
                }),
            ], md=2),
            # Graphs
            dbc.Col([
                html.Div([
                    dcc.Graph(figure=create_loss_distribution_graph(losses_distribution), style={'height': '38vh'})
                ], style={
                    'border': '2px solid',
                    'borderRadius': '5px',
                    'padding': '10px'
                }),
                html.Div([
                    dcc.Graph(figure=create_cvar_estimates_graph(losses_distribution), style={'height': '38vh'})
                ], style={
                    'border': '2px solid',
                    'borderRadius': '5px',
                    'padding': '10px',
                    'marginTop': '10px'
                })
            ], md=5),

            dbc.Col([
                html.Div([
                    dcc.Graph(figure=create_assign_losses_by_threat_graph(threat_losses_distribution),
                              style={'height': '38vh'})
                ], style={
                    'border': '2px solid',
                    'borderRadius': '5px',
                    'padding': '10px'
                }),
                html.Div([
                    dcc.Graph(figure=create_control_effectiveness_graph(unmitigated_losses, losses_distribution),
                              style={'height': '38vh'})
                ], style={
                    'border': '2px solid',
                    'borderRadius': '5px',
                    'padding': '10px',
                    'marginTop': '10px'
                })
            ], md=3),
        ], className="mb-0"),  # add margin-bottom CSS class
    ], fluid=True)

    app.run_server(debug=True, use_reloader=False)


# Define a function to open the web browser
def open_browser():
    time.sleep(1)  # Wait for a second to ensure the server has started
    webbrowser.open('http://127.0.0.1:8050/')


class ProgressWindow(QWidget):
    def __init__(self, parent=None):
        super(ProgressWindow, self).__init__(parent)
        self.setWindowTitle("Simulation Progress Tracker")
        self.resize(400, 200)  # Resize the window
        # This is the QTextEdit widget that we will use to print the iterations.
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.text_edit)

        self.setLayout(layout)


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Risk Simulation")
        self.resize(1250, 720)  # Resize the window

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.threats = QListWidget()
        self.harms = QListWidget()
        self.controls = QListWidget(self)
        self.iterations = QSpinBox()
        self.run_simulation_button = QPushButton('Run Simulation')

        self.add_threat_button = QPushButton('Add Threat')
        self.add_threat_button.clicked.connect(self.add_threat)
        self.add_harm_button = QPushButton('Add Harm')
        self.add_harm_button.clicked.connect(self.add_harm)
        self.add_control_button = QPushButton('Add Control')
        self.add_control_button.clicked.connect(self.add_control)

        self.threats.itemDoubleClicked.connect(self.edit_threat)
        self.harms.itemDoubleClicked.connect(self.edit_harm)
        self.controls.itemDoubleClicked.connect(self.edit_control)

        # Add the delete buttons
        self.delete_threat_button = QPushButton('Delete Threat')
        self.delete_threat_button.clicked.connect(self.delete_threat)
        self.delete_harm_button = QPushButton('Delete Harm')
        self.delete_harm_button.clicked.connect(self.delete_harm)
        self.delete_control_button = QPushButton('Delete Control')
        self.delete_control_button.clicked.connect(self.delete_control)

        self.initUI()
        self.init_defaults()

    def initUI(self):
        self.setWindowTitle('Simulation Program')
        self.setWindowIcon(QIcon('icon.png'))

        vbox = QVBoxLayout()

        vbox.addWidget(QLabel("Threats:"))
        vbox.addWidget(self.threats)
        vbox.addWidget(self.add_threat_button)
        vbox.addWidget(self.delete_threat_button)  # Add the delete button to the layout

        vbox.addWidget(QLabel("Harms:"))
        vbox.addWidget(self.harms)
        vbox.addWidget(self.add_harm_button)
        vbox.addWidget(self.delete_harm_button)  # Add the delete button to the layout

        vbox.addWidget(QLabel("Controls:"))
        vbox.addWidget(self.controls)
        vbox.addWidget(self.add_control_button)
        vbox.addWidget(self.delete_control_button)  # Add the delete button to the layout

        vbox.addWidget(QLabel("Total Number of Iterations:"))
        self.iterations.setRange(1, 999999)
        self.iterations.setSingleStep(100)
        vbox.addWidget(self.iterations)

        vbox.addWidget(self.run_simulation_button)

        self.central_widget.setLayout(vbox)

        self.run_simulation_button.clicked.connect(self.start_simulation)

        self.show()

    def add_threat(self):
        dialog = ThreatDialog(self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            name, type, case_count, probability, interval_probability, duration, interval_count, risk_level = dialog.getValues()
            self.threats.addItem(
                f'Name: {name}, Type: {type}, Case Count: {case_count}, Probability: {probability}, '
                f'Interval Probability: {interval_probability}, Duration: {duration}, Interval Count: {interval_count}, '
                f'Risk Level: {risk_level}')

    def add_harm(self):
        dialog = HarmDialog(self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            name, harm_type, magnitude, cost_lower_bound, cost_higher_bound, probability = dialog.getValues()
            self.harms.addItem(
                f'Name: {name}, Type: {harm_type}, Magnitude: {magnitude}, Cost (Min): {cost_lower_bound}, '
                f'Cost (Max): {cost_higher_bound}, Probability: {probability}')

    def add_control(self):
        dialog = ControlDialog(self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            standard, control_type, value, automated, overall_value, effectiveness = dialog.getValues()
            self.controls.addItem(
                f'Standard: {standard}, Type: {control_type}, Value: {value}, Automated: '
                f'{automated}, Overall Value: {overall_value}, Effectiveness: {effectiveness}')

    # Add delete methods
    def delete_threat(self):
        row = self.threats.currentRow()
        if row != -1:  # If no row is selected, currentRow() returns -1
            self.threats.takeItem(row)

    def delete_harm(self):
        row = self.harms.currentRow()
        if row != -1:
            self.harms.takeItem(row)

    def delete_control(self):
        row = self.controls.currentRow()
        if row != -1:
            self.controls.takeItem(row)

    def edit_threat(self, item):
        # Parse the text of the item
        name, type, case_count, probability, interval_probability, duration, interval_count, risk_level = self.parse_threat_text(item.text())
        # Create a dialog with the item's values
        dialog = EditThreatDialog(name, type, case_count, probability, interval_probability, duration, interval_count,
                                  risk_level, self)
        result = dialog.exec()
        # If the dialog is accepted, update the item with the new values
        if result == QDialog.Accepted:
            name, type, case_count, probability, interval_probability, duration, interval_count, risk_level = dialog.getValues()
            item.setText(
                f'Name: {name}, Type: {type}, Case Count: {case_count}, Probability: {probability}, '
                f'Interval Probability: {interval_probability}, Duration: {duration}, Interval Count: {interval_count}, '
                f'Risk Level: {risk_level}')

    def edit_harm(self, item):
        name, harm_type, magnitude, cost_lower_bound, cost_higher_bound, probability = self.parse_harm_text(item.text())
        dialog = EditHarmDialog(name, harm_type, magnitude, cost_lower_bound, cost_higher_bound, probability, self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            name, harm_type, magnitude, cost_lower_bound, cost_higher_bound, probability = dialog.getValues()
            item.setText(
                f'Name: {name}, Type: {harm_type}, Magnitude: {magnitude}, Cost (Min): {cost_lower_bound}, '
                f'Cost (Max): {cost_higher_bound}, Probability: {probability}')

    def edit_control(self, item):
        standard, control_type, value, automated, overall_value, effectiveness = self.parse_control_text(item.text())
        dialog = EditControlDialog(standard, control_type, value, automated, overall_value, effectiveness, self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            standard, control_type, value, automated, overall_value, effectiveness = dialog.getValues()
            item.setText(
                f'Standard: {standard}, Type: {control_type}, Value: {value}, Automated: '
                f'{automated}, Overall Value: {overall_value}, Effectiveness: {effectiveness}')

    @staticmethod
    def parse_threat_text(text):
        # Assumes the text is in the format "Name: {name}, Type: {type}, Case Count: {case_count}, Probability: {probability}, Interval Probability: {interval_probability}, Duration: {duration}, Interval Count: {interval_count}, Risk Level: {risk_level}"
        parts = text.split(',')
        name = parts[0].split(': ')[1]
        type = parts[1].split(': ')[1]
        case_count = int(parts[2].split(': ')[1])
        probability = float(parts[3].split(': ')[1])
        interval_probability = float(parts[4].split(': ')[1])
        duration = int(parts[5].split(': ')[1])
        interval_count = float(parts[6].split(': ')[1])
        risk_level = parts[7].split(': ')[1]
        return name, type, case_count, probability, interval_probability, duration, interval_count, risk_level

    @staticmethod
    def parse_harm_text(text):
        # Assumes the text is in the format "Name: {name}, Type: {type}, Magnitude: {magnitude}, Cost (Min): {cost_min}, Cost (Max): {cost_max}, Probability: {probability}"
        parts = text.split(',')
        name = parts[0].split(': ')[1]
        harm_type = parts[1].split(': ')[1]
        magnitude = parts[2].split(': ')[1]
        cost_lower_bound = float(parts[3].split(': ')[1])
        cost_higher_bound = float(parts[4].split(': ')[1])
        probability = parts[5].split(': ')[1]
        return name, harm_type, magnitude, cost_lower_bound, cost_higher_bound, probability

    @staticmethod
    def parse_control_text(text):
        # soup = BeautifulSoup(text, "html.parser")
        # text_no_html = soup.get_text()
        # parts = text_no_html.split(',')
        parts = text.split(',')
        standard = parts[0].split(': ')[1]
        control_type = parts[1].split(': ')[1]
        value = parts[2].split(': ')[1]
        automated = parts[3].split(': ')[1]
        overall_value = parts[4].split(': ')[1]
        effectiveness = float(parts[5].split(': ')[1])
        return standard, control_type, value, automated, overall_value, effectiveness

    def init_defaults(self):

        # Define default threats and harms dictionaries
        threats = {
            'T1': {'name': 'DDoS', 'type': 'Availability Attack', 'case_count': 7059, 'probability': 0.046795,
                   'interval_probability': 0.003358, 'duration': 458, 'interval_count': 91.6, 'risk_level': 'Medium'},
            'T2': {'name': 'Operational Incident', 'type': 'Operational Outage', 'case_count': 570, 'probability': 0.003779,
                   'interval_probability': 0.000271, 'duration': 135, 'interval_count': 27.0, 'risk_level': 'Low'}
        }

        harms = {
            'H1': {'name': 'Harm1', 'type': 'Operational Outage', 'magnitude': 'High', 'first_order': {'costs': range(40, 61)},
                   'PROBABLE': 'Medium'},
            'H2': {'name': 'Harm2', 'type': 'Availability Attack', 'magnitude': 'Medium',
                   'first_order': {'costs': range(40, 61)}, 'PROBABLE': 'Low'}
        }

        controls = {
            'C1': {'standard': 'CIS-20', 'type': 'Operational Outage', 'value': 'High', 'automated': 'Yes', 'overall_value': 'High',
                   'effectiveness': 0.7},
            'C2': {'standard': 'ISO 27001', 'type': 'Availability Attack', 'value': 'Medium', 'automated': 'No',
                   'overall_value': 'Low', 'effectiveness': 0.9},
        }

        for key, control in controls.items():
            standard = control['standard']
            control_type = control['type']
            value = control['value']
            automated = control['automated']
            overall_value = control['overall_value']
            effectiveness = control['effectiveness']
            self.controls.addItem(
                f'Standard: {standard}, Type: {control_type}, Value: {value}, Automated: {automated}, Overall Value: '
                f'{overall_value}, Effectiveness: {effectiveness}')

        # Add the threats and harms to their respective QListWidgets
        for key, threat in threats.items():
            name = threat['name']
            type = threat['type']
            case_count = threat['case_count']
            probability = threat['probability']
            interval_probability = threat['interval_probability']
            duration = threat['duration']
            interval_count = threat['interval_count']
            risk_level = threat['risk_level']
            self.threats.addItem(
                f'Name: {name}, Type: {type}, Case Count: {case_count}, Probability: {probability}, '
                f'Interval Probability: {interval_probability}, Duration: {duration}, Interval Count: {interval_count}, '
                f'Risk Level: {risk_level}')

        for key, harm in harms.items():
            name = harm['name']
            harm_type = harm['type']
            magnitude = harm['magnitude']
            cost_lower_bound = min(harm['first_order']['costs'])
            cost_higher_bound = max(harm['first_order']['costs'])
            probability = harm['PROBABLE']
            self.harms.addItem(
                f'Name: {name}, Type: {harm_type}, Magnitude: {magnitude}, Cost (Min): {cost_lower_bound}, '
                f'Cost (Max): {cost_higher_bound}, Probability: {probability}')

        # Set the default control effective probability and iterations
        self.iterations.setValue(100)


    def start_simulation(self):
        # Get current date and time
        current_date_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        """
        # Set up logging
        # log_filename = f"Log_{current_date_time}.log"
        log_filename = f"Simulation.log"

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            handlers=[logging.FileHandler(log_filename, 'w', 'utf-8')])

        # logging.info("Loading Data Successful")
        """
        # Create a logger object
        logger = logging.getLogger(__name__)

        # Check if the logger has any handlers and remove them if it does
        if logger.hasHandlers():
            logger.handlers.clear()

        # Set log level
        logger.setLevel(logging.INFO)

        # Create a file handler
        handler = logging.FileHandler('simulation.log')
        handler.setLevel(logging.INFO)

        # Create a logging format
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)

        # Add the handlers to the logger
        logger.addHandler(handler)

        # -------------------------------------- Acquiring simulation parameters ---------------------------------------

        threats = {}
        harms = {}
        controls = {}
        iterations = self.iterations.value()

        # Parse and create the threats dictionary
        for i in range(self.threats.count()):
            text = self.threats.item(i).text()
            name, harm_type, case_count, probability, interval_probability, duration, interval_count, risk_level = text.split(
                ', ')
            threats_key = 'T' + str(i + 1)  # Construct a threats key similar to 'T1', 'T2', etc.

            threats[threats_key] = {
                'name': name.split(': ')[1],
                'type': harm_type.split(': ')[1],
                'case_count': float(case_count.split(': ')[1]),
                'probability': float(probability.split(': ')[1]),
                'interval_probability': float(interval_probability.split(': ')[1]),
                'duration': int(duration.split(': ')[1]),
                'interval_count': float(interval_count.split(': ')[1]),
                'risk_level': risk_level.split(': ')[1],
            }

        # Parse and create the harms dictionary
        for i in range(self.harms.count()):
            text = self.harms.item(i).text()
            name, harm_type, magnitude, cost_lower_bound, cost_higher_bound, probability = text.split(', ')
            harms_key = 'H' + str(i + 1)  # Construct a harms key similar to 'H1', 'H2', etc.

            harms[harms_key] = {
                'name': name.split(': ')[1],
                'type': harm_type.split(': ')[1],
                'magnitude': magnitude.split(': ')[1],
                'first_order': {
                    'costs': range(int(cost_lower_bound.split(': ')[1]), int(cost_higher_bound.split(': ')[1]) + 1)},
                # Add 1 to include the high bound
                'PROBABLE': probability.split(': ')[1],
            }

        # Parse and create the controls dictionary
        for index in range(self.controls.count()):
            item = self.controls.item(index)
            standard, control_type, value, automated, overall_value, effectiveness = self.parse_control_text(
                item.text())
            controls_key = 'C' + str(index + 1)  # Construct a controls key similar to 'C1', 'C2', etc.

            controls[controls_key] = {
                'standard': standard,
                'type': control_type,
                'value': value,
                'automated': automated,
                'overall_value': overall_value,
                'effectiveness': effectiveness
            }

        # Here are the inputs acquired from the user:
        print(threats)  # A dictionary
        print(harms)  # A dictionary
        print(controls)  # A dictionary
        print(iterations)  # An int

        # ---------------------------- Please use the above 4 variables as your model input ----------------------------
        import pandas as pd

        scotia = pd.read_csv('./dataByBank/scotia_16_17.csv')

        scotias = scotia.sample(288)

        scotias['id'] = scotias.index

        result_list = []

        for index, row in scotias.iterrows():
            dictionary = {'name': 'Asset', 'id': 'A', 'cost': row['sum']}
            result_list.append(dictionary)

        dictionary = {}
        n = 0
        while n < len(result_list):
            dictionary['A' + str(n)] = result_list[n]
            n = n + 1

        scotia_dict = dictionary
        scotia = scotia_dict

        # Threats Data
        print(threats)  # A dictionary
        """
        threat_intervals = {
            'T1': [{'probability': threats['T1']['interval_probability']} for _ in
                   range(int(threats['T1']['interval_count']))],
            'T2': [{'probability': threats['T2']['interval_probability']} for _ in
                   range(int(threats['T2']['interval_count']))]
        }
        """
        threat_intervals = {}
        for threat_id, threat in threats.items():
            threat_intervals[threat_id] = [{'probability': threat['interval_probability']} for _ in
                                           range(int(threat['interval_count']))]

        # Asset Data
        assets = scotia
        # Assign a random value between 0.1 and 0.9
        for asset in assets.values():
            asset['loss_factor'] = random.uniform(0.1, 0.9)

        # Controls Data
        print(controls)  # A dictionary

        # Harms Data
        print(harms)  # A dictionary

        # This dictionary represents the assumed probabilities associated with each level of threat.
        # In this scenario, high threats are assumed to occur with 90% probability, medium threats
        # with 50%, and low threats with 10%.

        threat_probabilities = {'High': 0.9, 'Medium': 0.5, 'Low': 0.1}

        # threat_probabilities = {threat['risk_level']: threat['probability'] for threat in threats.values()}

        # This list represents the different types of threats considered in the risk assessment.
        # 'Outage' could represent a situation where the system becomes unavailable due to an external outage
        # (i.e., ROGERS Wireless) and 'Availability' might represent a threat where system availability is compromised,
        # for example through a Denial of Service (DoS) attack.
        """
        threat_types = ['Outage', 'Availability']
        """
        threat_types = list(set(threat['type'] for threat in threats.values()))

        # This list represents the different types of controls put in place to mitigate the risks.
        # In this scenario, the controls are categorized similarly to the threats for simplification.
        control_types = ['Outage', 'Availability']

        # Correlation Matrix
        # This 2x2 matrix indicates how closely related two threats are.
        """
        correlation_matrix = np.array([
            [1.0, 0.5],  # Correlation of Threat1 with itself and Threat2
            [0.5, 1.0]  # Correlation of Threat2 with Threat1 and itself
        ])
        """
        # Generate an identity matrix (perfect correlation with self, no correlation with others) of size equal to number of threats
        correlation_matrix = np.eye(len(threats))


        # Mean (probability) and standard deviation for each threat
        # We're setting these for Threat1 and Threat2.
        """
        threat_means = [threats['T1']['probability'], threats['T2']['probability']]
        threat_stds = [0.05, 0.05]  # replace with your actual standard deviations
        """
        threat_means = [threat['probability'] for threat in threats.values()]
        threat_stds = [0.05 for _ in threats.values()]  # Replace with your actual standard deviations

        # Convert correlation matrix to covariance matrix
        covariance_matrix = np.outer(threat_stds, threat_stds) * correlation_matrix

        def calculate_losses(assets, threats, controls, harms, threat_probabilities, threat_intervals):

            '''
            The parameters for this function are:
            assets: A dictionary representing 5-min sums of LVTS Transfers
            threats: A dictionary representing different types of threats
            controls: A dictionary representing measures taken to mitigate threats
            harms: A dictionary representing the harm that can be caused by a threat
            threat_probabilities: A dictionary representing the probabilities of different threat levels
            threat_intervals: A dictionary representing the intervals at which threats could happen
            '''

            # Initialize variables for total_loss, unmitigated_loss and threat_losses
            total_loss = 0
            unmitigated_loss = 0
            threat_losses = {}

            # Loop over each 5-min sum of LVTS transfers
            for asset in assets.values():

                # For each asset, we consider each possible threat
                for threat_id, threat in threats.items():

                    # Look for a corresponding harm for this threat
                    # If we don't find one, we move on to the next threat
                    harm = next((h for h in harms.values() if h['type'] == threat['type']), None)
                    if harm is None:
                        continue

                    # Look for a corresponding control for this threat
                    control = next((c for c in controls.values() if c['type'] == threat['type']), None)

                    # Randomly choose a cost from the list of possible harm costs
                    # This represents the potential loss if the threat happens
                    cost = np.random.choice(harm['first_order']['costs'])

                    # Calculate the value of the asset with a bit of randomness
                    asset_value = np.random.normal(asset['cost'], asset['cost'] * 0.1)

                    # Calculate the loss if the threat occurs (% of the value)
                    loss = asset_value * cost / 100
                    unmitigated_loss += loss * threat_probabilities[threat['risk_level']]

                    # If there is a control, and it's effective, calculate the mitigated loss
                    # The mitigated loss is the original loss reduced by the control's effectiveness
                    if control and control['effectiveness'] > 0:
                        effectiveness = np.random.normal(control['effectiveness'], 0.1)
                        mitigated_loss = loss * (1 - effectiveness)

                    else:
                        # If there's no control, the mitigated loss is the same as the original loss
                        mitigated_loss = loss

                    # Adjust the mitigated loss based on the threat's risk level
                    mitigated_loss *= threat_probabilities[threat['risk_level']]

                    # Get the interval probabilities for this threat
                    interval_probabilities = threat_intervals[threat_id]

                    # Loop over all intervals for this calculation
                    for interval in interval_probabilities:
                        interval_probability = interval['probability']

                        # Adjust the mitigated loss based on the interval's probability
                        mitigated_loss_interval = mitigated_loss * interval_probability

                        # If we've already calculated losses for this threat, we add to the total
                        # If not, we initialize the total for this threat
                        if threat_id in threat_losses:
                            threat_losses[threat_id] += mitigated_loss_interval * asset['loss_factor']
                        else:
                            threat_losses[threat_id] = mitigated_loss_interval * asset['loss_factor']

                        # Add the mitigated loss for this threat and asset to the total loss
                        total_loss += mitigated_loss_interval * asset['loss_factor']

            # Return the total loss, unmitigated loss and per-threat losses
            return total_loss, unmitigated_loss, threat_losses

        # sample from a multivariate normal distribution based on a correlation matrix that
        #  \describes the relationships between different threats

        def run_simulation(num_iterations, threat_probabilities, threat_intervals, covariance_matrix, threat_means,
                           seed=123):
            np.random.seed(seed)
            results = []
            unmitigated_losses = []
            threat_losses_distribution = {threat_id: [] for threat_id in threats.keys()}

            # Generate samples from a multivariate normal distribution
            """
            samples = np.random.multivariate_normal(threat_means, covariance_matrix, size=num_iterations)
            """
            samples = np.random.multivariate_normal(threat_means, covariance_matrix, size=num_iterations)

            """
            for i in range(num_iterations):
                print(f"Iteration {i}")
                QApplication.processEvents()  # Allow GUI to update
                window.text_edit.append(f"Iteration {i}/{num_iterations}")
                # Extract sample for current iteration
                sample = samples[i]

                # Update the probabilities of the threats based on the sample
                threats['T1']['probability'] = sample[0]
                threats['T2']['probability'] = sample[1]
            """
            for i in range(num_iterations):
                print(f"Iteration {i}")
                QApplication.processEvents()  # Allow GUI to update
                window.text_edit.append(f"Iteration {i}/{num_iterations}")
                # Extract sample for current iteration
                sample = samples[i]

                # Update the probabilities of the threats based on the sample
                for j, threat_id in enumerate(threats):
                    threats[threat_id]['probability'] = sample[j]

                # Calculate losses
                losses, unmitigated_loss, threat_losses = calculate_losses(assets, threats, controls, harms,
                                                                           threat_probabilities, threat_intervals)
                results.append(losses)
                unmitigated_losses.append(unmitigated_loss)

                for threat_id, loss in threat_losses.items():
                    threat_losses_distribution[threat_id].append(loss)

            print(f"Impact: {results}")
            print(f"Unmitigated Losses: {results}")
            return results, unmitigated_losses, threat_losses_distribution

        # Running the simulation (Pick Run Value)
        num_iterations = iterations

        window = ProgressWindow()
        window.show()

        losses_distribution, unmitigated_losses, threat_losses_distribution = run_simulation(num_iterations,
                                                                                             threat_probabilities,
                                                                                             threat_intervals,
                                                                                             covariance_matrix,
                                                                                             threat_means, 123)

        # Run dashboard

        # These are the input to the model
        avg_loss = np.array(losses_distribution).mean().round(2)
        std_loss = np.array(losses_distribution).std().round(2)
        percentile_95 = np.percentile(losses_distribution, 95).round(2)
        percentile_99 = np.percentile(losses_distribution, 99).round(2)
        cvar_95 = np.mean([loss for loss in losses_distribution if loss >= percentile_95]).round(2)
        cvar_99 = np.mean([loss for loss in losses_distribution if loss >= percentile_99]).round(2)
        static_fields = [iterations, f"$ {avg_loss}", f"$ {std_loss}", f"$ {percentile_95}", f"$ {cvar_95}", f"$ {cvar_99}"]
        static_fields_names = ["Number of Iterations", "Average Impact", "SD of Impact", "VaR @ 5%",
                               "Conditional VaR @ 5%", "Conditional VaR @ 1%"]
        incident_types = []
        for threat in threats.values():
            incident_types.append(threat['name'])
        institutions = ["Institution 1", "Institution 2", "Institution 3", "Institution 4", "Institution 5"]

        log_message = f"Number of iterations: {iterations}, Average Impact: $ {avg_loss}, SD of Impact: $ {std_loss}, " \
                      f"VaR @ 5%: $ {percentile_95}, Conditional VaR @ 5%: $ {cvar_95}, Conditional VaR @ 1%: $ {cvar_99}"
        logger.info(log_message)


        dash_thread = threading.Thread(target=run_dash_server,
                                       name=f"Thread-dash",
                                       args=(losses_distribution, threat_losses_distribution, unmitigated_losses,
                                             static_fields, static_fields_names, incident_types, institutions))

        dash_thread.start()

        # get a list of all alive threads
        threads = threading.enumerate()

        for thread in threads:
            print(f"Thread name: {thread.name}")


        # run the open browser function in another thread
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.start()




if __name__ == '__main__':
    qt_app = QApplication(sys.argv)
    ex = MyApp()
    print('Application launch successful')
    sys.exit(qt_app.exec_())





















