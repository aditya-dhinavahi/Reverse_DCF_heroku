import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input,Output, State
import dash_bootstrap_components as dbc
from apps import val,home
from app import app,server
#import required apps here

dropdown = dbc.DropdownMenu(children=[dbc.DropdownMenuItem("Home",href="/home"),
	#dbc.DropdownMenuItem("Visualization",href="/visualization"),
	#dbc.DropdownMenuItem("Table",href="/table"),
	dbc.DropdownMenuItem("DCF Valuation",href="/val")],
	nav=True,
	in_navbar=True,
	label="Pages")

navbar = dbc.Navbar(
	dbc.Container(
		[html.A(
			dbc.Row(
				[
				dbc.Col(dbc.NavbarBrand("Reverse DCF",className="ml-2")),
				],
				align="center",
				
				),
			href = "/home"),
		dbc.NavbarToggler(id="navbar-toggler2"),
		dbc.Collapse(
			dbc.Nav(
				[dropdown],className="ml-auto",navbar=True),
			id="navbar-collapse2",
			navbar=True,
			),
		]
		),
	color="dark",
	dark=True,
	className="mb-4"
	)

def toggle_navbar_collapse(n,is_open):
	if n:
		return not is_open
	return is_open

for i in [2]:
	app.callback(
		Output(f"navbar-collapse{i}","is_open"),
		[Input(f"navbar-toggler{i}","n_clicks")],
		[State(f"navbar-collapse{i}","is_open")],
		)(toggle_navbar_collapse)


app.layout = html.Div([
	dcc.Location(id="url",refresh=False),
	navbar,
	html.Div(id="page-content")
	])

@app.callback(Output("page-content","children"),
	[Input("url","pathname")])
def display(pathname):
	if pathname== "/val":
		return val.layout
	else:
		return home.layout

if __name__=="__main__":
	app.run_server(debug=True)