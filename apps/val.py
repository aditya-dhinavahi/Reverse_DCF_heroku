#Required imports
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Output,Input
from dash import callback
import pandas as pd
import requests
from bs4 import BeautifulSoup
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy.spatial import Delaunay
cpe = 0
fy20pe = 0
def scrape(symbol):
    URL = "https://screener.in/company/"+symbol+"/consolidated"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content,"html.parser")
    results = soup.findAll("span",attrs={'class':"number"})
    if(len(results)==0):
        return -1,-1,-1,-1,-1
    if(len(results[0])==0):
        URL = "https://screener.in/company/"+symbol
        page = requests.get(URL)
        soup = BeautifulSoup(page.content,"html.parser")
        results = soup.findAll("span",attrs={'class':"number"})
        if(len(results)==0):
            return -1,-1,-1,-1,-1
        initial_params = [float(results[0].text.replace(",","")),float(results[4].text.replace(",",""))]
    initial_params = [float(results[0].text.replace(",","")),float(results[4].text.replace(",",""))]
    results = soup.findAll("section",attrs={"id":"profit-loss"})
    df = pd.read_html(results[0].table.prettify())
    net_profit = float(df[0].iloc[-3,-2])
    fy20pe = initial_params[0]/net_profit
    results = soup.findAll("table",attrs={"class":"ranges-table"})
    csg = pd.read_html(results[0].prettify())[0].iloc[:,-1].str.replace("%","").values
    cpg = pd.read_html(results[1].prettify())[0].iloc[:,-1].str.replace("%","").values
    results = soup.findAll("section",attrs={"id":"ratios"})
    roce = pd.read_html(results[0].table.prettify())[0].iloc[-1].dropna().iloc[-6:-1].str.replace("%","").astype("float32").values
    roce_median = np.median(roce)
    return initial_params[1],fy20pe,csg,cpg,roce_median


def dcf(coc,roce,gdhgp,tgr,fp,hgp):
    tax_rate = 0.25
    coc = coc/100
    roce = roce/100
    roce = roce * (1-tax_rate)
    gdhgp = gdhgp/100
    tgr = tgr/100
    rr1 = gdhgp/roce
    rr2 = tgr/roce
    cap_emp = 100
    prev_cap_emp = 100
    egr = 0
    nopat = 0
    prev_nopat = 0
    investment = 0
    fcf = 0
    disc_factor = 0
    disc_fcf = 0
    disc_fcf_li = []
    init_nopat = 0
    #High Growth Period formulas
    #Earnings growth rate = (nopat(i)/prev_nopat(i-1)-1) for i>=1
    #NOPAT = Prev_Cap * roce
    #Cap_Emp = Prev_Cap_Emp + Investment
    #Investment = NOPAT*RR1
    #FCF = NOPAT - Investment
    #Disc_Factor = 1/(1+coc)**i
    #Disc_fcf = fcf*disc_factor
    for i in range(hgp+1):
        if(i>0):
            egr = (nopat/prev_nopat) - 1
            prev_nopat = nopat
        
        nopat = cap_emp*roce
        if(i==0):
            init_nopat = nopat
            prev_nopat = nopat
        prev_cap_emp = cap_emp
        investment = nopat * rr1
        cap_emp = cap_emp + investment
        fcf = nopat - investment
        disc_factor = (1/(1+coc))**i
        disc_fcf = fcf * disc_factor
        disc_fcf_li.append(disc_fcf)

    #Fade Growth period formulas
    #Earnings growth rate = prev_egr-(gdhgp-tgr)/fp
    #Investment = next_egr/roce*nopat
    #Rest of them are same as High Growth period
    next_egr = 0
    for i in range(hgp+1,hgp+fp+1):
        egr = egr-((gdhgp-tgr)/fp)
        #next_egr = egr-((gdhgp-tgr)/fp)
        nopat = cap_emp*roce

        investment = (egr/roce)*nopat
        cap_emp = cap_emp + investment
        fcf = nopat - investment
        disc_factor = (1/(1+coc))**i
        disc_fcf = fcf * disc_factor
        disc_fcf_li.append(disc_fcf)
    terminal_nopat = (nopat*(1+tgr))/(coc-tgr)
    terminal_investment = terminal_nopat*rr2
    terminal_fcf = terminal_nopat - terminal_investment
    terminal_disc_factor = disc_factor
    terminal_disc_fcf = terminal_fcf * terminal_disc_factor
    disc_fcf_li.append(terminal_disc_fcf)
    intrinsic_val = sum(disc_fcf_li)
    calc_iPE = intrinsic_val/init_nopat
    return calc_iPE

"""external_stylesheets = [
    {
        "href": "./style.css",
        "rel": "stylesheet",
    },
]
app = dash.Dash(__name__,external_stylesheets=external_stylesheets)
server=app.server
app.title = "Valuing Consistent Compounders"""

layout = html.Div(children=[html.H1(children="Valuing Consistent Compounders",),html.P(children="Hi there!",),html.P(children="This page will help you calculate intrinsic PE of consistent compounders through growth-RoCE DCF model.",),html.P(children="We then compare this with current PE of the stock to calculate degree of overvaluation.",),
    
    html.Div(children=[
    html.Div(children = [html.Div(children="NSE/BSE symbol",className="menu-title"),dcc.Input(id="symbol2",type="text",value="NESTLEIND"),]),
    html.Div(children=[html.Div(children="Cost of Capital (CoC): %",className="menu-title"),dcc.Slider(id="coc2",min=8,max=16,step=0.5,marks={8:"8",9:"9",10:"10",11:"11",12:"12",13:"13",14:"14",15:"15",16:"16"},value=12)]),
    html.Div(children=[html.Div(children="Return on Capital Employed (RoCE): %",className="menu-title"),dcc.Slider(id="roce2",min=10,max=100,step=5,marks={10:"10",20:"20",30:"30",40:"40",50:"50",60:"60",70:"70",80:"80",90:"90",100:"100"},value=20)]),
    html.Div(children=[html.Div(children="Growth during high growth period: $",className="menu-title"),dcc.Slider(id="gdhgp2",min=8,max=20,step=1,marks={8:"8",10:"10",12:"12",14:"14",16:"16",18:"18",20:"20"},value=12)]),
    html.Div(children=[html.Div(children="High growth period(years)",className="menu-title"),dcc.Slider(id="hgp2",min=10,max=25,step=1,marks={10:"10",12:"12",14:"14",16:"16",18:"18",20:"20",22:"22",24:"24",25:"25"},value=15)]),
    html.Div(children=[html.Div(children="Fade period(years): ",className="menu-title"),dcc.Slider(id="fp2",min=5,max=20,step=5,marks={5:"5",10:"10",15:"15",20:"20"},value=15)],className="four columns div-user-controls"),
    html.Div(children=[html.Div(children="Terminal growth rate: %",className="menu-title"),dcc.Slider(id="tgr2",min=0,max=7.5,step=0.5,marks={0:"0",1:"1",2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",7.5:"7.5"},value=5)])]
    ),html.P(children="",id="stock_res2",style={'whiteSpace':'pre-wrap'}),
    dash_table.DataTable(id="stock_res_table2",columns = [],data=[]),
    html.Div(children=[dcc.Graph(id="stock_res_graph_3")],style={'width':'47.5%',"display":'inline-block'}),
    html.Div(children=[dcc.Graph(id="stock_res_graph_4")],style={'width':'47.5%',"display":'inline-block'}),
    html.P(children="",id="calc_res2",style={'whiteSpace':'pre-wrap'}),],
    
    
    )

@callback(
    [Output("stock_res2","children"),Output("stock_res_table2","columns"),Output("stock_res_table2","data"),Output("calc_res2","children"),Output("stock_res_graph_3","figure"),Output("stock_res_graph_4","figure")],
    [Input("symbol2","value"),
    Input("coc2","value"),
    Input("roce2","value"),
    Input("gdhgp2","value"),
    Input("hgp2","value"),
    Input("fp2","value"),
    Input("tgr2","value")]
    )

def update_stock(symbol,coc,roce,gdhgp,hgp,fp,tgr):
    cpe,fy20pe,csg,cpg,roce_median = scrape(symbol)
    if(cpe==-1):
        return "Error",[],[],"Error"
    ciPE = dcf(coc,roce,gdhgp,tgr,fp,hgp)
    if(cpe<fy20pe):
        dov = ((cpe/ciPE)-1)*100
        pe_diff = ciPE - cpe
        points = [ciPE,cpe]
    else:
        dov = ((fy20pe/ciPE-1)*100)
        pe_diff = ciPE - fy20pe
        points = [ciPE,fy20pe]
    csg_int = [float(i) for i in csg]
    cpg_int = [float(i) for i in cpg]
    fig = px.bar(x=csg_int,y=["10 yrs","5 yrs","3 yrs","TTM"],orientation="h",range_x=[min(csg_int)-2,max(csg_int)+2],labels=dict(x="Sales Growth (%)",y="Time Period"))
    fig_pg = px.bar(x=cpg_int,y=["10 yrs","5 yrs","3 yrs","TTM"],orientation="h",range_x=[min(cpg_int)-2,max(cpg_int)+2],labels=dict(x="Profit Growth (%)",y="Time Period"))
    #csg_int = [int(i) for i in csg]
    #fig.update_xaxes({'range':[min(csg_int)-2,max(csg_int)+2]})
    #fig.update_xaxes({'tickmode':'array','tickvals':[i for i in range(min(csg_int)-2,max(csg_int)+3)]})

    return "Stock Symbol: " + symbol + "\nCurrent PE: "+str(round(cpe,2))+"\nFY23PE: "+str(round(fy20pe,1))+"\n5-yr median pre-tax RoCE: "+str(round(roce_median,2))+"%",[{'name':" ",'id':" "},{'name':"10 yrs",'id':"10 yrs"},{'name':"5yrs",'id':'5yrs'},{'name':"3yrs",'id':'3yrs'},{'name':"TTM",'id':'TTM'}],[{" ":"Sales Growth","10 yrs":str(csg[0]),"5yrs":str(csg[1]),"3yrs":str(csg[2]),"TTM":str(csg[3])},{" ":"Profit growth","10 yrs":str(cpg[0]),"5yrs":str(cpg[1]),"3yrs":str(cpg[2]),"TTM":str(cpg[3])}],"Play with inputs to see changes in intrinsic PE and overvaluation:\nThe calculated intrinsic PE is: "+str(round(ciPE,2))+"\nDegree of overvaluation: "+str(round(dov))+"%",fig,fig_pg

