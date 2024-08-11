# Simulator-for-traders
This is a free (test) simulator for technical analysis of cryptocurrencies for traders
I decided to make a free simulator for crypto traders. I want to share with you a script that you can use for any of your purposes, but if you have a desire to develop this project, then please help) Programmers can rewrite something and share it for improvement, and traders can write what to add because you know something).

At the moment, the script works as follows:
It takes a random period for the last week, and builds a chart with a candlestick interval of 15 minutes, then the trader is offered to open a trade in long/short and click on the 'next step' button, each click on the button extends the chart for 1 hour (maximum 5 clicks) after which the trader will see his profit/loss in $ and percentages

necessary libraries:
pip install dash dash-bootstrap-components yfinance plotly pandas
