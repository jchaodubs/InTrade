import json
import openai 
import pandas as pd 
import matplotlib.pyplot as plt 
import streamlit as st 
import yfinance as yf
import base64

#read api key
openai.api_key = open('API_KEY','r').read()

def get_stock_price(ticker):
    return str(yf.Ticker(ticker).history(period='1y').iloc[-1].Close)

def calculate_SMA(ticker, window):#Simple moving average
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.rolling(window=window).mean().iloc[-1])

def calculate_EMA(ticker, window):# Exponential moving average
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.ewm(span=window,adjust=False).mean().iloc[-1])

def calculate_RSI(ticker):# relative strength index
    data = yf.Ticker(ticker).history(period='1y').Close
    delta = data.diff()
    up = delta.clip(lower=0)
    down = -1*delta.clip(upper=0)
    ema_up = up.ewm(com = 14-1,adjust=False).mean()
    ema_down=down.ewm(com=14-1,adjust=False).mean()
    rs = ema_up / ema_down
    return str(100-(100/ (1+rs)).iloc[-1])

def calculate_MACD(ticker):#moving average convergence divergence
    data = yf.Ticker(ticker).history(period='1y').Close
    short_EMA = data.ewm(span=12, adjust=False).mean()
    long_EMA = data.ewm(span=26, adjust = False).mean()

    MACD = short_EMA - long_EMA
    signal = MACD.ewm(span=9, adjust= False).mean()
    MACD_histogram = MACD - signal
    
    return f'{MACD[-1]}, {signal[-1]}, {MACD_histogram[-1]}'

def plot_stock_price(ticker):
    data = yf.Ticker(ticker).history(period='1y')
    plt.figure(figsize = (10,5))
    plt.plot(data.index, data.Close)
    plt.title(f'{ticker} Stock Price Over Last Year')
    plt.xlabel('Date')
    plt.ylabel('Stock Price($)')
    plt.grid(True)
    plt.savefig('stock.png')
    plt.close()



#parameters for open ai to use the functions set
#warning: new name stocks (ie meta instead of fb) may not be found
functions = [
    {
        'name': 'get_stock_price',
        'description': 'Gets the latest stock price given the ticker symbol of a company.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol for a company (for example AAPL for Apple). Note: FB is renamed to META'
                }
            },
            'required': ['ticker']
        },
    },
    {
        "name": "calculate_SMA",
        "description": "Calculate the simple moving average for a given stock ticker and a window.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for a company (e.g., AAPL for Apple)",
                },
                "window": {
                    "type": "integer",
                    "description": "The timeframe to consider when calculating the SMA"
                }
            },
            "required": ["ticker", "window"]
        },
    },
    {
        "name": "calculate_EMA",
        "description": "Calculate the exponential moving average for a given stock ticker and a window.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for a company (e.g., AAPL for Apple)",
                },
                "window": {
                    "type": "integer",
                    "description": "The timeframe to consider when calculating the EMA"
                }
            },
            "required": ["ticker", "window"]
        },
    },
    {
        "name": "calculate_RSI",
        "description": "Calculate the RSI for a given stock ticker.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for a company (e.g., AAPL for Apple)",
                }
            },
            "required": ["ticker"]
        },
    },
    {
        "name": "calculate_MACD",
        "description": "Calculate the MACD for a given stock ticker.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for a company (e.g., AAPL for Apple)",
                }
            },
            "required": ["ticker"]
        },
    },
    {
        "name": "plot_stock_price",
        "description": "Plot the stock price for the last year given the ticker symbol of a company",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol for a company (e.g., AAPL for Apple)",
                }
            },
            "required": ["ticker"]
        },
    },
]

available_functions={
    'get_stock_price': get_stock_price,
    'calculate_SMA': calculate_SMA,
    'calculate_EMA': calculate_EMA,
    'calculate_RSI': calculate_RSI,
    'calculate_MACD': calculate_MACD,
    'plot_stock_price': plot_stock_price

}
#creates streamlit site
st.set_page_config(page_title='InStock', initial_sidebar_state = 'auto')
if 'messages' not in st.session_state:
    st.session_state['messages']=[]

st.title('Stock Analysis Chatbot')
#design, credits and blocks out header/footer
custom_footer= """
    <div style="position: fixed; bottom: 26px;text-align: center; background-color: rgba(248, 249, 250, 0.5);  border-radius: 5px 5px 5px 5px;">
    <p style="margin: 0;">Contact: jchao11@ucsc.edu</p>
    </div>
    <div style="position: fixed; bottom: 0;text-align: center; background-color: rgba(248, 249, 250, 0.5);  border-radius: 5px 5px 5px 5px;">
    <p style="margin: 0;">Made by Jeffrey Chao, Made possible by Jacob Shin and Ian Dang</p>
    </div>
    <style>
       footer,header {visibility: hidden;}
       </style>
       """
st.markdown(custom_footer, unsafe_allow_html=True)
def set_bg_hack_url():
    #background image
        
    st.markdown(
         f"""
         <style>
         .stApp {{
             background: url("https://upload.wikimedia.org/wikipedia/commons/5/55/McHenry_Library_UCSC.jpg");
             background-size: cover
             
         }}
         </style>
         """,
         unsafe_allow_html=True
     )
set_bg_hack_url()
user_input = st.text_input("Your input: (e.g. What is the stock price of Apple?)")

if user_input:#for when someone types something
    try:
        st.session_state['messages'].append({'role': 'user', 'content': f'{user_input}'})

        response = openai.ChatCompletion.create(
            model = 'gpt-3.5-turbo-0613',
            messages = st.session_state['messages'],
            functions = functions,
            function_call = 'auto'
        )

        response_message = response['choices'][0]['message']

        if response_message.get('function_call'):
            function_name = response_message['function_call']['name']
            function_args = json.loads(response_message['function_call']['arguments'])
            if function_name in ['get_stock_price','calculate_RSI','calculate_MACD', 'plot_stock_price']:
                args_dict = {'ticker': function_args.get('ticker')}
            elif function_name in ['calculate_SMA','calculate_EMA']:
                args_dict = {'ticker': function_args.get('ticker'),'window': function_args.get('window')}

            function_to_call = available_functions[function_name]
            function_response = function_to_call(**args_dict)

            if function_name == 'plot_stock_price':
                st.image('stock.png')
            else:
                st.session_state['messages'].append(response_message)
                st.session_state['messages'].append(
                    {
                        'role': 'function',
                        'name' : function_name,
                        'content' : function_response
                    }
                )
                second_response = openai.ChatCompletion.create(
                    model = 'gpt-3.5-turbo-0613',
                    messages = st.session_state['messages']
                )

                assistant_response = second_response['choices'][0]['message']['content']
                st.markdown(
                    f'<div class="assistant-response">{assistant_response}</div>',
                    unsafe_allow_html=True
                )
                st.session_state['messages'].append({'role': 'assistant', 'content': assistant_response})


                #st.text(second_response['choices'][0]['message']['content'])
                #st.session_state['messages'].append({'role':'assistant','content': second_response['choices'][0]['message']['content']})

                st.markdown(# marks answer with background color
                """
                <style>
                .assistant-response {
                    background-color: #f0f0f0; /* Change to the desired background color */
                    padding: 10px;
                    border-radius: 5px;
                    word-wrap: break-word;
                }
                </style>
                """,
                unsafe_allow_html=True
)
        else:
            st.text(response_message['content'])
            st.session_state['messages'].append({'role': 'assistant','content': response_message['content']})
    except Exception as e:
        st.text('Error occured, '+str(e))


        

