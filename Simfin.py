import pandas as pd
import numpy as np
import _pickle as pickle
import seaborn as sns

# TensorFlow and Keras imports.
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import Sequential
from tensorflow.keras.optimizers import RMSprop
from tensorflow.keras.layers import Dense, InputLayer
from tensorflow.keras.utils import to_categorical

# Scikit-learn imports.
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
from sklearn.metrics import r2_score, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight

# Import the main functionality from the SimFin Python API.
import simfin as sf

# Import names used for easy access to SimFin's data-columns.
from simfin.names import *

# SimFin data-directory.
sf.set_data_dir('~/simfin_data/')

# SimFin load API key or use free data.
sf.load_api_key(path='~/simfin_api_key.txt', default_key='free')

# Seaborn set plotting style.
sns.set_style("whitegrid")

# We are interested in the US stock-market.
market = 'us'

# Add this date-offset to the fundamental data such as
# Income Statements etc., because the REPORT_DATE is not
# when it was actually made available to the public,
# which can be 1, 2 or even 3 months after the Report Date.
offset = pd.DateOffset(days=60)

# Refresh the fundamental datasets (Income Statements etc.)
# every 30 days.
refresh_days = 30

# Refresh the dataset with shareprices every 10 days.
refresh_days_shareprices = 10

hub = sf.StockHub(market=market, offset=offset,
                  refresh_days=refresh_days,
                  refresh_days_shareprices=refresh_days_shareprices)

df_price_signals = hub.price_signals()
df_vol_signals = hub.volume_signals(window=20)
df_fin_signals_daily = hub.fin_signals(variant='daily')
df_growth_signals_daily = hub.growth_signals(variant='daily')
df_val_signals_daily = hub.val_signals(variant='daily')
df_prices = hub.load_shareprices(variant='daily')

# List of all the DataFrames with different signals.
dfs = [df_price_signals, df_fin_signals_daily,
       df_growth_signals_daily, df_val_signals_daily]
df_signals = pd.concat(dfs, axis=1)

# Remove all rows with only NaN values.
df_signals = df_signals.dropna(how='all').reset_index(drop=True)

# Name of the new Pandas Series with the stock-returns.
TOTAL_RETURN_1_3Y = 'Total Return 1-3 Years'

df_returns_1_3y = \
    hub.mean_log_returns(name=TOTAL_RETURN_1_3Y,
                         min_years=1, max_years=3,
                         future=True, annualized=True)

dfs = [df_signals, df_returns_1_3y]
df_sig_rets = pd.concat(dfs, axis=1)

# Clip both the signals and returns at their 5% and 95% quantiles.
# We do not set them to NaN because it would remove too much data.
df_sig_rets = sf.winsorize(df_sig_rets)

# Remove all rows with missing values (NaN)
# because TensorFlow cannot handle that.
df_sig_rets = df_sig_rets.dropna(how='any')

# Remove all tickers which have less than 200 data-rows.
df_sig_rets = df_sig_rets.groupby(TICKER) \
                .filter(lambda df: len(df)>200)

# List of all unique stock-tickers in the dataset.
tickers = df_sig_rets.reset_index()[TICKER].unique()

# Split the tickers into training- and test-sets.
tickers_train, tickers_test = \
    train_test_split(tickers, train_size=0.8, random_state=1234)

df_train = df_sig_rets.loc[tickers_train]
df_test = df_sig_rets.loc[tickers_test]

# DataFrames with signals for training- and test-sets.
X_train = df_train.drop(columns=[TOTAL_RETURN_1_3Y])
X_test = df_test.drop(columns=[TOTAL_RETURN_1_3Y])

# DataFrames with returns for training- and test-sets.
y_train = df_train[TOTAL_RETURN_1_3Y]
y_test = df_test[TOTAL_RETURN_1_3Y]

num_signals = X_train.shape[1]


# This so-called "activation function" is applied after each layer.
# It is important to use a non-linear function, otherwise
# the Neural Network cannot learn non-linear mappings.
activation = 'relu'

# Create a new Keras model.
model_regr = Sequential()

# Add an input layer for the signals.
# Note how we set the dimensionality of the input here.
model_regr.add(InputLayer(input_shape=(num_signals,)))

# Add several dense aka. fully-connected layers.
# You can experiment with different designs.
model_regr.add(Dense(128, activation=activation))
model_regr.add(Dense(64, activation=activation))
model_regr.add(Dense(32, activation=activation))
model_regr.add(Dense(16, activation=activation))
model_regr.add(Dense(8, activation=activation))

# Add a layer for the output of the Neural Network.
# This is 1-dimensional to match the stock-return data.
model_regr.add(Dense(1))

# Compile the model but don't train it yet.
model_regr.compile(loss='mse', metrics=['mae'],
                   optimizer=RMSprop(0.001))

# Show the model.
model_regr.summary()

fit_args = \
    {
        # For efficiency, the model is trained on batches of data.
        'batch_size': 4096,

        # Number of iterations aka. epochs over the training-set.
        'epochs': 40,

        # Fraction of the training-set used for validation after
        # each training-epoch, to assess how well the model performs
        # on unseen data.
        'validation_split': 0.2,

        # Show status during training.
        'verbose': 1,
    }

history_regr = model_regr.fit(x=X_train.values,
                              y=y_train.values, **fit_args)

y_train_pred = model_regr.predict(X_train.values)
y_test_pred = model_regr.predict(X_test.values)

r2_score(y_true=y_train, y_pred=y_train_pred)
r2_score(y_true=y_test, y_pred=y_test_pred)

# Column-name for the models' predicted stock-returns.
TOTAL_RETURN_PRED = 'Total Return Predicted'

# Create a DataFrame with actual and predicted stock-returns.
# This is for the training-set.
df_y_train = pd.DataFrame(y_train)
df_y_train[TOTAL_RETURN_PRED] = y_train_pred


# Calculate the correlation between all signals and stock-returns.
df_corr = df_sig_rets.corr()

# Show how the signals are correlated with the stock-returns.
# Sorted to show the strongest absolute correlations first.
df_corr_returns = df_corr[TOTAL_RETURN_1_3Y].abs().sort_values(ascending=False)
print(df_corr_returns)