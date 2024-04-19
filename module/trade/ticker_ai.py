import os
import json
import datetime

from module.trade.ticker import Ticker

from pydantic import BaseModel, Field
from llama_index.core import PromptTemplate
from llama_index.core import ChatPromptTemplate
from llama_index.core.llms import ChatMessage

from llama_index.experimental.query_engine import PandasQueryEngine


from llama_index.llms.openai import OpenAI


class yFinanceQuery(BaseModel):
    """Data model for a yFinance APIs."""

    rationale: str = Field(
        description="Please provide the brief rationale behind why you did you provide the details for the symbol, start date, end date, interval to retrieve data based on the user question. Please provide why you are querying specific interval data."
    )
    symbol: str = Field(
        description="The symbol of the stock or index for which data has to be queried"
    )
    start_date: str = Field(
        description="The start date of the data to be queried. The date must be in the format 'YYYY-MM-DD' / %Y-%m-%d format. Start date cannot be same as end date."
    )
    end_date: str = Field(
        description="The end date of the data to be queried. The date must be in the format 'YYYY-MM-DD' / %Y-%m-%d format. For Current date, it is safer to provide the end_date as the next day of the current date. End date cannot be same as start date."
    )
    interval: str = Field(
        description="The interval of the data to be queried. Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo. Intraday data (1m, 2m, 5m, 15m, 30m) cannot extend last 60 days. 60m, 90m, 1h data cannot extend 700 days. Default is '1d'"
    )   


yfinance_query_template = PromptTemplate("""
You are a search query builder for yFinance APIs based on the user question.
Based on the user question, you will need to form a search query that will be used to search and retrieve the data from the yFinance APIs.
Current date is {current_date}.
Current time is {current_time}.
                                         
Please provide the following details in a JSON format. The details are as follows:
- rationale : Please provide the brief rationale behind why you did you provide the details for the symbol, start date, end date, interval to retrieve data based on the user question. Please provide why you are querying specific interval data.
- symbol : The symbol of the stock or index for which data has to be queried
- start_date : The date must be in the format 'YYYY-MM-DD' / %Y-%m-%d format. Start date cannot be same as end date.
- end_date : The date must be in the format 'YYYY-MM-DD' / %Y-%m-%d format. For Current date, it is safer to provide the end_date as the next day of the current date. End date cannot be same as start date.
- interval : The interval of the data to be queried. Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo. Intraday data (1m, 2m, 5m, 15m, 30m) cannot extend last 60 days. 60m, 90m, 1h data cannot extend 700 days. Default is '1d'

User Questions is provided below:
{question}                                                            
""")


synthesis_template = PromptTemplate("""
You are a stock market response synthesizer based on the user question, API query, pandas query and result.

User Question: {question}

Based on the user question, following API query is generated for which yFinance data is fetched.

API Query: {api_query}
                                    
Based on the API query, the yFinance data is fetched and the data is queried using the following pandas query.
                                    
Pandas Query: {pandas_query}
                                    
Based on the pandas query, the result is generated as follows.
                                    
Result: {result}
                                    
Please provide the final response for the user question based on the above. Provide good reasoning about why you have provided the answer.
If the user questions is not releveant to stock market, then API query, pandas query and result will be bad. So, you can request users to ask questions related to stock market in a humourous way.
""")


class TickerAI():
    def __init__(self, llm=None):

        if llm is None:
            llm = OpenAI(
                temperature=0.9,
                model=os.getenv("OPENAI_CHAT_MODEL"),
                api_key=os.getenv("OPENAI_API_KEY"),
                max_retries=3,
                verbose=True,
            )
            self.llm = llm
        else:
            self.llm = llm
        
    def get_api_arguments(self, question=""):
        try:
            # Create the search system prompt
            system_prompt = yfinance_query_template.format(
                question=question,
                current_date=datetime.datetime.now().strftime('%Y-%m-%d'),
                current_time=datetime.datetime.now().strftime('%H:%M:%S')
            )

            # Create a chat prompt
            prompt = ChatPromptTemplate(
                message_templates=[
                    ChatMessage(
                        role="system",
                        content=system_prompt
                    )
                ]
            )

            # Format the messages and output schema
            messages = prompt.format_messages(
                json_schema=yFinanceQuery.model_json_schema()
            )

            output = self.llm.chat(
                messages, response_format={"type": "json_object"}
            ).message.content

        except Exception as e:
            print(f"Error getting API JSON arguments: {e}")
            return None
        
        print(f"Response from the AI for Arguments: {output}")
        output_dict = json.loads(output)

        # Validate the output
        validated_output = self.validate_api_arguments(output_dict)

        if validated_output:
            return output_dict
        else:
            return output_dict

    def validate_api_arguments(self, output_dict):
        try:
            if output_dict['rationale'] is None or output_dict['rationale'] == "":
                raise ValueError("Rationale is required")

            # Validate the symbol
            if not Ticker.is_valid_symbol(output_dict['symbol']):
                raise ValueError(f"Invalid symbol {output_dict['symbol']}")
            
            # Validate the start date
            start_date = datetime.datetime.strptime(output_dict['start_date'], '%Y-%m-%d')

            # Validate the end date
            end_date = datetime.datetime.strptime(output_dict['end_date'], '%Y-%m-%d')

            # Validate the interval
            valid_intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
            if output_dict['interval'] not in valid_intervals:
                raise ValueError(f"Invalid interval {output_dict['interval']}")
            
            # for start date and end date greater than 700, supported intervals are 1d, 5d, 1wk, 1mo, 3mo
            if (end_date - start_date).days > 700 and output_dict['interval'] not in ['1d', '5d', '1wk', '1mo', '3mo']:
                raise ValueError(f"Invalid interval for the given date range {output_dict['interval']}")
            
            return True
            
        except Exception as e:
            print(f"Error validating the API arguments: {e}")
            return False

    def query_yfinance_data(self, dataframe, question=""):
        """
        Query yFinance data based on the user question
        """
        try:
            query_engine = PandasQueryEngine(df=dataframe, verbose=True, llm=self.llm)
            response = query_engine.query(question)
            return response.response, response.metadata
        except Exception as e:
            print(f"Error querying the yFinance data: {e}")
            raise "Error querying the yFinance data. Please provide a valid question."

    def synthesis(self, question="", api_arguments=None, pandas_query=None, result=None):
        """
        Synthesize the response based on the question, API arguments, pandas query and result
        """
        try:
            system_prompt = synthesis_template.format(
                question=question,
                api_query=json.dumps(api_arguments),
                pandas_query=pandas_query,
                result=result
            )

            # Create a chat prompt
            messages = [
                    ChatMessage(
                        role="system",
                        content=system_prompt
                    )
                ]

            # Format the messages and output schema
            response = self.llm.chat(messages).message.content
            return str(response)
        except Exception as e:
            print(f"Error synthesizing the response: {e}")
            raise "Error synthesizing the response. Please provide a valid question."

    def chat(self, question=""):
        """
        Chat with the AI to get the API arguments
        """

        # Get the API arguments
        arguments = self.get_api_arguments(question)

        response = ""
        query = ""

        try:
            symbol = arguments['symbol']
            start_date = arguments['start_date']
            end_date = arguments['end_date']
            interval = arguments['interval']
            
            Ticker_obj = Ticker(symbol=symbol)
            historical_data = Ticker_obj.get_historical_data(start_date, end_date, interval)

            # Query the data
            response, query = self.query_yfinance_data(historical_data, question)
        
        except Exception as e:
            print(f"Error getting historical data, querying the data or synthesizing the response: {e}")
        
        finally:
            # Synthesize the response
            try:
                final_response = self.synthesis(question, arguments, query, response)
                return final_response
            except Exception as e:
                print(f"Error synthesizing the response: {e}")
                return "There is some error in synthesizing the response currently. Could you please try again?"