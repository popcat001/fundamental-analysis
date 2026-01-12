## Phase 1: Data preparation
I want to design a tool to help with fundamental analysis for stock trading. It contains
1. A UI to visualize all the information
2. A database to store the important financial data for a company

On the UI, there is a place where i can input a stock ticker, then it will show the following data in the past 8 quarters (2 years)
* EPS
* Free cash flow
* gross income / margin
* new income / margin
* Capex
* Cash balance / debt

It will first search the database for those information. If none is found or some information is missing, then it will go online to get those information to display and store then into the database.  


## Phase 2: valuation module (P/E method)
Create a stock valuation module using the P/E multiple method

For a given ticker

1. Get Forward EPS
	Estimate its forward looking EPS from historical data
2. Determine **justified P/E** from peers + history + fundamentals
1) P/E history: Price at reporting date / ((EPS at corresponding quarter)*4)
2) historical EPS/Revenue Growth rate


### Phase 2.1: access the backend data
I want to be able to access/visualize the backend data used for the valuation analysis whenever i want to (on demand). For example, in part 1. forward EPS calculation, i want to know the historical EPS used for the calculation; in part 2, i want to know the historical P/E for last 5 quarters (EPS, price and P/E on the plot); so on until part 4.