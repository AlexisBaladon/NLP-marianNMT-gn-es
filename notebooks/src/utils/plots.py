import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

DATE_COL = 'date'
SCORE_TYPE_COL = 'score_type'
SCORE_COL = 'score'
EPOCH_COL = 'epoch'
MODEL_ID = 'model_name'
DURATION_COL = 'duration'

def plot_metrics_by_epoch(dataframe, metrics, save_path=None):
    num_metrics = len(metrics)
    
    sns.set(style='darkgrid')
    _, axes = plt.subplots(ncols=num_metrics, figsize=(4*num_metrics, 4))
    
    for i, metric in enumerate(metrics):
        ax = axes[i]
        sns.lineplot(x='epoch', y=metric, data=dataframe, ax=ax)
        ax.set_title(metric)

        highest_value = dataframe[metric].max()
        max_index = dataframe[dataframe[metric] == highest_value]['epoch'].values[0]
        ax.plot(max_index, 
                highest_value, 
                marker='o', 
                markersize=8, 
                color='red')
        ax.text(0, 
                highest_value, 
                f'Epoch: {int(max_index-1)} \n Max: {highest_value:.2f}', 
                ha='center', 
                va='bottom', 
                color='black', 
                bbox=dict(facecolor='white', alpha=1, edgecolor='black'))
    
    plt.tight_layout()
    plt.savefig(save_path) if save_path is not None else plt.show()

def plot_metric_by_x_foreach_model(df, 
                                   x,
                                   by='x',
                                   title=None,
                                   metric=None, 
                                   metrics=None, 
                                   figsize=(12, 8), 
                                   legend=True, 
                                   save_path=None,
                                   model_name=MODEL_ID,
                                   score_name=SCORE_COL,
                                   tight_layout=True):
    if metrics is None:
        metrics = [metric]

    sns.set(style='darkgrid')
    fig, ax = plt.subplots(figsize=figsize, ncols=len(metrics), nrows=1)

    for idx, metric in enumerate(metrics):
        ax_i = ax[idx] if len(metrics) > 1 else ax
        metric_df = df[df[SCORE_TYPE_COL] == metric]
        
        sns.lineplot(x=x, 
                     y=score_name, 
                     hue=model_name, 
                     data=metric_df, 
                     errorbar=None, 
                     legend=legend, 
                     ax=ax_i)

        ax_i.set_ylabel(metric)
        ax_i.set_xlabel(x[0].upper() + x[1:])

        if tight_layout:
            plt.tight_layout()

    if title is None:
        source = df["source"].unique()[0]
        source = 'gn' if 'gn' in source else 'es'
        target = df["target"].unique()[0]
        target = 'gn' if 'gn' in target else 'es'
        architecture = df[model_name].unique()[0]
        architecture = 's2s' if 's2s' in architecture else 'transformer'

        title = f'Metric comparison by {by} for direction {source}->{target} and {architecture} architecture'
        fig.suptitle(title)
    else:
        fig.suptitle(title)
    
    plt.subplots_adjust(top=0.95)


    plt.savefig(save_path) if save_path is not None else plt.show()

def plot_metric_by_epoch_foreach_model(df, 
                                       metric=None, 
                                       metrics=None, 
                                       figsize=(12, 8), 
                                       legend=True, 
                                       save_path=None,
                                       title=None,
                                       model_name=MODEL_ID,
                                       score_name=SCORE_COL,
                                       tight_layout=True):
    plot_metric_by_x_foreach_model(df, 
                                   EPOCH_COL, 
                                   title=title,
                                   by='epoch',
                                   metric=metric, 
                                   metrics=metrics, 
                                   figsize=figsize, 
                                   legend=legend, 
                                   save_path=save_path,
                                   model_name=model_name,
                                   score_name=score_name,
                                   tight_layout=tight_layout)

def plot_metric_by_time_foreach_model(df,
                                      metric=None, 
                                      metrics=None, 
                                      figsize=(12, 8), 
                                      save_path=None):
    plot_metric_by_x_foreach_model(df,
                                   DATE_COL, 
                                   by='time',
                                   metric=metric, 
                                   metrics=metrics, 
                                   figsize=figsize, 
                                   save_path=save_path)

def create_df_from_results_csv(results_csv_path):
    df = pd.read_csv(results_csv_path)
    return df

def plot_max_score_by_model(df: pd.DataFrame, 
                            title=None,
                            by='model',
                            metrics=None, 
                            metric=None, 
                            figsize=(20, 6), 
                            save_path=None, 
                            y_col=MODEL_ID, 
                            sort_by=SCORE_COL, 
                            ascending=False,
                            model_name=MODEL_ID,
                            score_name=SCORE_COL):
    if metrics is None:
        metrics = [metric]
    
    fig, ax = plt.subplots(figsize=figsize, 
                           ncols=len(metrics), 
                           nrows=1)

    for idx, metric in enumerate(metrics):
        ax_i = ax[idx] if len(metrics) > 1 else ax
        metric_df = df[df[SCORE_TYPE_COL] == metric]
        group_cols = [score_name] + ([sort_by] if sort_by != score_name else [])
        metric_df = metric_df.groupby(model_name)[group_cols].max().reset_index()
        metric_df = metric_df.sort_values(by=sort_by, ascending=ascending)
        sns.set(style='darkgrid')
        sns.barplot(x=score_name, y=y_col, data=metric_df, ax=ax_i, palette='coolwarm')
        ax_i.set_xticklabels(ax_i.get_xticklabels()) #, rotation=45)
        ax_i.set_xlabel(metric)

        for j in ax_i.containers:
            ax_i.bar_label(j,)

    if title is None:
        source = df["source"].unique()[0]
        source = 'gn' if 'gn' in source else 'es'
        target = df["target"].unique()[0]
        target = 'gn' if 'gn' in target else 'es'
        architecture = df[model_name].unique()[0]
        architecture = 's2s' if 's2s' in architecture else 'transformer'

        title = f'Metric comparison by {by} for direction {source}->{target} and {architecture} architecture'
        fig.suptitle(title)
        
        # More space to title
        plt.subplots_adjust(top=0.85)

    plt.tight_layout()
    plt.savefig(save_path) if save_path is not None else plt.show()

def plot_time_by_model(df: pd.DataFrame, 
                       title: str, 
                       duration_col=DURATION_COL, 
                       figsize=(20, 6), 
                       save_path=None):
    df = df.sort_values(by=duration_col, ascending=False)
    sns.set(style='darkgrid')
    plt.figure(figsize=figsize)
    ax = sns.barplot(x=MODEL_ID, y=duration_col, data=df)

    for i in ax.containers:
        ax.bar_label(i,)

    plt.title(title)
    plt.tight_layout()
    plt.xticks(rotation=45)
    plt.savefig(save_path) if save_path is not None else plt.show()

def plot_values_by_index(title, values, color=None, ax=None):
    sns.set_style('darkgrid')
    y = list(range(len(values)))
    x = values

    if ax is None:
        plt.figure(figsize=(20, 6))
        ax = sns.lineplot(x=x, y=y, color=color)
    else:
        ax.plot(x, y, color=color)

    ax.set_title(title)
    ax.set_xlabel('Index')
    ax.set_ylabel('Value')
    plt.tight_layout()

    if ax is None:
        plt.show()