#! /bin/python3

def setup_logging(config):
  '''
  Logging is a stanbdard python library and this code is for setting
  up logger from yaml configuration section logger
  INFO or DEBUG logs more or less datailsed data, the default is info
  The three options for file stream of bot selects logging to file or
  printing to the console or doing both.
  The last option os the logging string format. The string format is
  covered in detaoils in the logger documentation.
  '''

  #print(f'logger config: {config}')
  if config['level']=='INFO':
    lvl=logging.INFO
  elif config['level']=='DEBUG':
    lvl=logging.DEBUG
  else:
    lvl=logging.NOTSET
  if config['handler'] == 'file':
    lhandlers=[
      logging.FileHandler(filename=config['filepath'], mode=config['filemode'])
    ]
  elif config['handler'] == 'stream':
    lhandlers=[
      logging.StreamHandler()
    ]
  elif config['handler'] == 'both':
    lhandlers=[
      logging.FileHandler(filename=config['filepath'], mode=config['filemode']),
      logging.StreamHandler()
    ]
  logging.basicConfig(
    level=lvl,
    format=config['format'],
    handlers=lhandlers
    )
  #logging.getLogger().addHandler(logging.StreamHandler())
  logging.getLogger(__name__)
  #iFormat=IndentFormatter(config['format'])
  #lhandlers[0].setFormatter(iFormat)
  #lhandlers[1].setFormatter(iFormat)
  return logging

def create_file_list(rootfolder=None, verbose=False):
  import os

  folder_path = "logfiles"  # Replace with the actual folder path
  # Get the list of files in the folder
  file_list = os.listdir(folder_path)
  # Print the file names
  if verbose:
    for file_name in file_list:
      logging.debug(file_name)
  return file_list


def create_plot(df):
  import matplotlib.pyplot as pl
  import seaborn as sns
  import matplotlib.dates as mdates
  from datetime import datetime
  
  if len(df) >100000:
    resample='5T'
    rolling_mean=96
  elif len(df) >5000:
    resample='30s'
    rolling_mean=120
  else:
    resample='5s'
    rolling_mean=120
  
  logging.info(f'creating plot - data length: {len(df)}')
  df.set_index('datetime', inplace=True)
  df=df.resample(resample).mean().fillna(0)
  #sns.lineplot(x='datetime', y='wind_speed', data=df)
  sns.scatterplot(x='datetime', y='wind_speed_ms', data=df, marker='.',legend='full')
  df['moving_avg'] = df['wind_speed_ms'].rolling(rolling_mean).mean()
  df['moving_avg_2']=df.apply(lambda v: v['moving_avg']*2, axis=1)
  sns.lineplot(x='datetime', y='moving_avg' , data=df, color='red', legend='auto')
  #sns.lineplot(x='datetime', y='moving_avg_2' , data=df, color='orange', legend='auto')
  
  #sns.set_style("whitegrid")
  #sns.set_context("paper")
  #sns.set(rc={'axes.grid': True, 'axes.grid.axis': 'y', 'axes.grid.which': 'major'})
  pl.grid(axis='y', color='lightgrey')
  pl.legend(labels=['speed(m/s)','moving avg'])#,loc="upper right")
  pl.title(f'Updated: {datetime.now()} UTC')
  #num_labels = 6
  #ticks, labels = pl.xticks()
  #step_size = len(df['datetime']) // (num_labels - 1)
  #pl.xticks(ticks[::step_size])
  #pl.gca().set_xticklabels(labels[::step_size])
  date_format = mdates.DateFormatter('%d %b %H:%M')
  pl.gca().xaxis.set_major_formatter(date_format)
  
  pl.subplots_adjust(bottom=0.18)
  pl.xticks(rotation=18)
  return pl
  

def generate_plots():
  from datetime import datetime
  import pandas as pd
  #import matplotlib.pyplot as pl
  from scipy.stats import zscore
  from numpy import abs
  
  files=create_file_list()
  files.sort()
  dfs=[]
  for file in files:
    logging.debug(f'combine - {file}')
    df=pd.read_csv(f'logfiles/{file}')
    #df=df[abs(zscore(df['wind_speed_ms'])) < 5].reset_index()
    df=df[abs(zscore(df['wind_speed_ms'])) < 0.115].reset_index()
    dfs.append(df)
  df_all=pd.concat(dfs, ignore_index=True)
  df_all['datetime'] = df_all['datetime'].str.replace(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})$', r'\1.000', regex=True)
  df_all['datetime']=pd.to_datetime(df_all['datetime'], errors='ignore')
  df_all.to_feather('df_all.feather')
  #df_all=df_all.sort_values('datetime').reset_index()
  #print(df_all.head())
  #print(df_all.dtypes)
  pl=create_plot(df_all)
  if pl is not None:
    logging.debug(f'saving combined plot to file plot_all.png')
    pl.savefig(f'plots/plot_all.png')
    pl.close()
  #return df_all
  logging.debug(f'files: {files} ==> {files[-1]}')
  #file='231012'
  
  for filename in files[-1:]: # only the last file in the list
    file,ext=filename.split('.')
    logging.info(f'loading wind speed data from {file}.{ext} into dataframe')
    df=pd.read_csv(f'logfiles/{file}.csv')
    df['datetime'] = df['datetime'].str.replace(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})$', r'\1.000', regex=True)
    df['datetime']=pd.to_datetime(df['datetime'], errors='ignore')
    df=df[abs(zscore(df['wind_speed_ms'])) < 3].reset_index()
    plot=create_plot(df)
    if plot is not None:
      logging.debug(f'saving plot to file {file}.png')
      plot.savefig(f'plots/plot_{file}.png')
      plot.close()
    logging.info(f'processing completed')

def main():
  global logging
  from yaml import unsafe_load as yaml_load
  import logging
  cwd='/home/weather'
  with open(f'{cwd}/create_plots.yaml') as fp:
    config=yaml_load(fp)
  logging = setup_logging(config['logger'])
  # Suppress the _findfont_cached logging
  logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
  logging.info('='*100)
  logging.info(f'Config Loaded, loggining initialised...')
  logging.debug(f'cwd: {cwd}')
  from datetime import datetime
  logging.info(f'{datetime.now()} loading plotting libraries')
  
  return generate_plots()

if __name__ == '__main__':
  logging=None
  df=main()
