import dash_bootstrap_components as dbc 
import dash

external_stylesheets = [dbc.themes.LUX]

app = dash.Dash(__name__,external_stylesheets=external_stylesheets)

server = app.server
app.title = "Reverse DCF"
app.config.suppress_callback_exceptions = True
