# Numpy Python module is used in this file.
#   Licence: BSD-3-Clause License
#   Link: https://github.com/numpy/numpy

# Pandas Python module is used in this file.
#   Licence: BSD-3-Clause License
#   Link: https://github.com/pandas-dev/pandas

# Plotly Python module is used in this file.
#   Licence: MIT License
#   Link: https://github.com/plotly/plotly.py

import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import plotly.io as pio
from .._holder import DataHolder
from ..metrics import ActivityMetric, TransitionMetric, IdMetric, TraceMetric, UserMetric


def get_continuous_color(colorscale, intermed):
    if intermed <= 0 or len(colorscale) == 1:
        return colorscale[0][1]
    if intermed >= 1:
        return colorscale[-1][1]
    for cutoff, color in colorscale:
        if intermed > cutoff:
            low_cutoff, low_color = cutoff, color
        else:
            high_cutoff, high_color = cutoff, color
            break
    return px.colors.find_intermediate_color(lowcolor=low_color,
                                             highcolor=high_color,
                                             intermed=((intermed - low_cutoff) / (high_cutoff - low_cutoff)),
                                             colortype='rgb')


class ChartPainter:
    """
    Creates different types of interactive graphs using the Plotly library.

    Parameters
    ----------
    data: pandas.DataFrame or sberpm.DataHolder or sberpm.metrics instance
        Data to use for visualization.

    template: str, default='plotly'
        Name of the figure template. The following themes are available:
        'ggplot2', 'seaborn', 'simple_white', 'plotly', 'plotly_white',
        'plotly_dark', 'presentation', 'xgridoff', 'ygridoff', 'gridon',
        'none'.

    palette: str, default='sequential.Sunset_r'
        Name of the graph color palette. Must be the name of the Plotly
        continuous (sequential, diverging or cylclical) color scale
        from 'plotly.express.colors' submodules.

    Examples
    --------
    >>> from sberpm.visual import ChartPainter
    >>> from sberpm.metrics import ActivityMetric
    >>> activity_metric = ActivityMetric(data_holder, time_unit='d')
    >>> painter = ChartPainter(activity_metric)
    >>> painter.bar(x=data_holder.activity_column, y='total_duration',
    >>>             sort='total_duration', n=50)
    """

    def __init__(self,
                 data,
                 template='plotly',
                 palette='sequential.Sunset_r'):
        if type(data) is DataHolder:
            self._data = data.data
        elif type(data) == pd.DataFrame:
            self._data = data
        elif type(data) in [ActivityMetric, TransitionMetric, IdMetric, TraceMetric, UserMetric]:
            self._data = data.apply()
        else:
            raise TypeError
        pio.templates.default = template
        px.defaults.color_discrete_sequence = eval('px.colors.' + palette)
        px.defaults.color_continuous_scale = eval('px.colors.' + palette)
        self._colors, _ = px.colors.convert_colors_to_same_type(eval('px.colors.' + palette))
        self._colorscale = px.colors.make_colorscale(self._colors)

    def hist(self, x, color=None, subplots=None, barmode='stack', nbins=50, cumulative=False, orientation='v',
             opacity=0.8, edge=False, title='auto', slider=False, **kwargs):
        """
        Plots a histogram.

        Parameters
        ----------
        x: str or list of str
            Name of the column to make graph for. If it takes a list of
            column names, the input data is considered as wide-form
            rather than long-form.

        color: str, default=None
            Name of the column used to set color to bars.

        subplots: (rows, cols, ncols), default=None
            Creates a set of subplots:
            - rows: name of the column to use for constructing subplots
              along the y-axis.
            - cols: name of the column to use for constructing subplots
              along the x-axis.
            - ncols: number of columns of the subplot grid.

        barmode: {'stack', 'overlay', 'group'}, default='stack'
            Display mode of the bars with the same position coordinate.
            - If 'stack', the bars are stacked on top of each other.
            - If 'overlay', the bars are plotted over each other.
            - If 'group', the bars are placed side by side.

        nbins: int, default=50
            Number of bins.

        cumulative: bool, default=False
            Whether to plot a cumulative histogram.

        orientation: {'v', 'h'}, default='v'
            Orientation of the graph: 'v' for vertical and 'h' for horizontal.
            If 'h', the values are drawn along the y-axis.

        opacity: float, default=0.8
            Opacity of the bars. Ranges from 0 to 1.

        edge: bool, default=False
            Whether to draw bar edges.

        title: str, default='auto'
            Title of the graph. When 'auto', the title is generated automatically.

        slider: bool, default=False
            Whether to add a range slider to the plot.

        **kwargs: optional
            See 'plotly.express.histogram' for other possible arguments.

        Returns
        -------
        plotly.graph_objects.Figure
        """
        data = self._data
        if barmode == 'stack':
            barmode = 'relative'
        if orientation == 'v':
            y = None
        else:
            y = x
            x = None
        if subplots:
            facet_row, facet_col, facet_col_wrap = subplots[0], subplots[1], subplots[2]
        else:
            facet_row, facet_col, facet_col_wrap = None, None, None
        if color:
            len_labels = data[color].nunique()
            nums = np.linspace(0, len_labels, len_labels) / len_labels
            color_discrete_sequence = [get_continuous_color(self._colorscale, z) for z in nums]
        else:
            color_discrete_sequence = None
        fig = px.histogram(data_frame=data,
                           x=x,
                           y=y,
                           color=color,
                           facet_row=facet_row,
                           facet_col=facet_col,
                           facet_col_wrap=facet_col_wrap,
                           color_discrete_sequence=color_discrete_sequence,
                           barmode=barmode,
                           nbins=nbins,
                           cumulative=cumulative,
                           opacity=opacity,
                           orientation=orientation,
                           **kwargs)
        if edge is True:
            fig.update_traces(marker=dict(line=dict(color='black', width=1)))
        if title == 'auto':
            if type(x) != list:
                title = f'Histogram of {x}'
            else:
                title = 'Histogram'
        if type(x) == list:
            legend = dict(orientation='h', x=0.5, xanchor='center', y=1.01, yanchor='bottom', title=None)
            margin = dict(l=0, r=0, t=80, b=0)
        else:
            legend = {}
            margin = dict(l=0, r=0, t=50, b=0)
        fig.update_layout(title=dict(text=title, x=0.5, xref='paper'),
                          legend=legend,
                          margin=margin)
        if slider is True:
            fig.update_xaxes(rangeslider_visible=True)
        fig.show()

    def bar(self, x=None, y=None, sort=None, n=None, color=None, subplots=None, barmode='stack', agg=None,
            add_line=None, text=False, orientation='auto', opacity=1, edge=False, title='auto', slider=False, **kwargs):
        """
        Makes a bar chart.

        Parameters
        ----------
        x: str or list of str, default=None
            Name of the column to draw on the x-axis. If it takes a list of
            column names, the input data is considered as wide-form
            rather than long-form.

        y: str or list of str, default=None
            Name of the column to draw on the y-axis. If it takes a list of
            column names, the input data is considered as wide-form
            rather than long-form.

        sort: str, default=None
            Name of the column to sort values by in descending (ascending)
            order if 'n' is positive (negative).

        n: int, default=None
            Number of sorted rows to draw. If positive, the rows are sorted in
            descending order; if negative, the rows are sorted in ascending order.

        color: str, default=None
            Name of the column used to set color to bars.

        subplots: (rows, cols, ncols), default=None
            Creates a set of subplots:
            - rows: name of the column to use for constructing subplots
              along the y-axis.
            - cols: name of the column to use for constructing subplots
              along the x-axis.
            - ncols: number of columns of the subplot grid.

        barmode: {'stack', 'overlay', 'group'}, default='stack'
            Display mode of the bars with the same position coordinate.
            - If 'stack', the bars are stacked on top of each other.
            - If 'overlay', the bars are plotted over each other.
            - If 'group', the bars are placed side by side.

        agg: {'count', 'sum', 'avg', 'min', 'max'}, default=None
            Name of the function used to aggregate 'y' ('x') values if
            orientation is set to 'v' ('h').

        add_line: list of str, default=None
            List of column names to add line to the graph for. Each line
            will be drawn along a separate y-axis.

        text: bool, default=False
            Whether to show text labels in the figure.

        orientation: {'auto', 'v', 'h'}, default='auto'
            Orientation of the graph: 'v' for vertical and 'h' for horizontal.
            By default, it is determined automatically based on the input
            data types.

        opacity: float, default=1
            Opacity of the bars. Ranges from 0 to 1.

        edge: bool, default=False
            Whether to draw bar edges.

        title: str, default='auto'
            Title of the graph. When 'auto', the title is generated automatically.

        slider: bool, default=False
            Whether to add a range slider to the plot.

        **kwargs: optional
            See 'plotly.express.bar' for other possible arguments.

        Returns
        -------
        plotly.graph_objects.Figure
        """
        if x is None and y is None:
            raise ValueError("Either 'x' or 'y' must be given")
        data = self._data
        if sort:
            if n > 0:
                data = data.sort_values(by=sort, ascending=False).head(n)
            elif n < 0:
                data = data.sort_values(by=sort, ascending=True).head(n)
        if type(x) != list and type(y) != list:
            if y and pd.api.types.is_numeric_dtype(data[y]):
                continuous, categorical = y, x
                autorange = True
                if pd.api.types.is_integer_dtype(data[y]):
                    texttemplate = '%{y:.f}'
                else:
                    texttemplate = '%{y:.2f}'
            else:
                continuous, categorical = x, y
                autorange = 'reversed'
                if pd.api.types.is_integer_dtype(data[x]):
                    texttemplate = '%{x:.f}'
                else:
                    texttemplate = '%{x:.2f}'
        else:
            continuous, categorical = None, None
            if y and type(y) == list and pd.api.types.is_numeric_dtype(data[y[0]]):
                if pd.api.types.is_integer_dtype(data[y]):
                    texttemplate = '%{y:.f}'
                else:
                    texttemplate = '%{y:.2f}'
                autorange = True
            else:
                if pd.api.types.is_integer_dtype(data[x]):
                    texttemplate = '%{x:.f}'
                else:
                    texttemplate = '%{x:.2f}'
                autorange = 'reversed'
        if barmode == 'stack':
            barmode = 'relative'
        if orientation == 'auto':
            orientation = None
        if subplots:
            facet_row, facet_col, facet_col_wrap = subplots[0], subplots[1], subplots[2]
        else:
            facet_row, facet_col, facet_col_wrap = None, None, None
        if color:
            len_labels = data[color].nunique()
            nums = np.linspace(0, len_labels, len_labels) / len_labels
            color_discrete_sequence = [get_continuous_color(self._colorscale, z) for z in nums]
            color_discrete_map = {}
        else:
            color_discrete_map = {}
            color_discrete_sequence = None
            if categorical and data[categorical].nunique() == len(data):
                len_labels = len(data[categorical])
                nums = np.linspace(0, len_labels, len_labels) / len_labels
                color = [get_continuous_color(self._colorscale, z) for z in nums]
                color_discrete_map = 'identity'
        if add_line:
            opacity = 0.8
            color = None
            color_discrete_map = {}
            color_discrete_sequence = None
        if agg:
            fig = px.histogram(data_frame=data,
                               x=x,
                               y=y,
                               color=color,
                               facet_row=facet_row,
                               facet_col=facet_col,
                               facet_col_wrap=facet_col_wrap,
                               color_discrete_sequence=color_discrete_sequence,
                               color_discrete_map=color_discrete_map,
                               barmode=barmode,
                               opacity=opacity,
                               histfunc=agg,
                               orientation=orientation,
                               **kwargs)
            fig.update_layout(bargap=0.2)
        else:
            fig = px.bar(data_frame=data,
                         x=x,
                         y=y,
                         color=color,
                         facet_row=facet_row,
                         facet_col=facet_col,
                         facet_col_wrap=facet_col_wrap,
                         color_discrete_sequence=color_discrete_sequence,
                         color_discrete_map=color_discrete_map,
                         barmode=barmode,
                         opacity=opacity,
                         orientation=orientation,
                         **kwargs)
            if add_line and continuous and categorical:
                fig.data[-1].name = continuous
                layout_a = {}
                for i, a in enumerate(add_line):
                    if categorical == x:
                        x_a = data[x]
                        y_a = data[a]
                    else:
                        y_a = data[y]
                        x_a = data[a]
                    fig.add_trace(go.Scatter(x=x_a,
                                             y=y_a,
                                             name=a,
                                             mode='lines',
                                             marker_color=px.colors.qualitative.Plotly[i + 1 % 10],
                                             line_width=3,
                                             yaxis='y' + str(i + 2)))
                    layout_a[f'yaxis{i + 2}'] = dict(title=a, overlaying='y', anchor='free', side='right',
                                                     showgrid=False, position=1 - i * 0.07,
                                                     titlefont=dict(color=px.colors.qualitative.Plotly[i + 1 % 10]),
                                                     tickfont=dict(color=px.colors.qualitative.Plotly[i + 1 % 10]))
                fig.update_traces(hovertemplate=None,
                                  showlegend=True)
                fig.update_layout(hovermode='x',
                                  xaxis_domain=[0, 1 - 0.07 * (len(add_line) - 1)],
                                  **layout_a)
        if text is True:
            fig.update_traces(texttemplate=texttemplate,
                              textposition='outside',
                              selector=dict(type='bar'))
        else:
            fig.update_traces(textposition='none',
                              selector=dict(type='bar'))
        if edge is True:
            fig.update_traces(marker=dict(line=dict(color='black', width=0.5)))
        if title == 'auto':
            if continuous:
                title = f'Bar Chart of {continuous}'
            else:
                title = 'Bar Chart'
        if type(x) == list or type(y) == list or add_line:
            legend = dict(orientation='h', x=0.5, xanchor='center', y=1.01, yanchor='bottom', title=None)
            margin = dict(l=0, r=0, t=80, b=0)
        else:
            legend = {}
            margin = dict(l=0, r=0, t=50, b=0)
        fig.update_layout(title=dict(text=title, x=0.5, xref='paper'),
                          legend=legend,
                          margin=margin,
                          yaxis_autorange=autorange)
        if slider is True:
            fig.update_xaxes(rangeslider_visible=True)
        fig.show()

    def box(self, x=None, y=None, color=None, subplots=None, boxmode='group', points='outliers', orientation='auto',
            title='auto', **kwargs):
        """
        Makes a box plot.

        Parameters
        ----------
        x: str or list of str, default=None
            Name of the column to draw on the x-axis. If it takes a list of
            column names, the input data is considered as wide-form
            rather than long-form.

        y: str or list of str, default=None
            Name of the column to draw on the y-axis. If it takes a list of
            column names, the input data is considered as wide-form
            rather than long-form.

        color: str, default=None
            Name of the column used to set color to boxes.

        subplots: (rows, cols, ncols), default=None
            Creates a set of subplots:
            - rows: name of the column to use for constructing subplots
              along the y-axis.
            - cols: name of the column to use for constructing subplots
              along the x-axis.
            - ncols: number of columns of the subplot grid.

        boxmode: {'group', 'overlay'}, default='group'
            Display mode of the boxes with the same position coordinate.
            - If 'group', the boxes are placed side by side.
            - If 'overlay', the boxes are plotted over each other.

        points: {'all', 'outliers', 'suspectedoutliers', 'False'},
            default='outliers'
            Type of underlying data points to display. Can be either all points,
            outliers only, suspected outliers only, or none of them.

        orientation: {'auto', 'v', 'h'}, default='auto'
            Orientation of the graph: 'v' for vertical and 'h' for horizontal.
            By default, it is determined automatically based on the input
            data types.

        title: str, default='auto'
            Title of the graph. When 'auto', the title is generated automatically.

        **kwargs: optional
            See 'plotly.express.box' for other possible arguments.

        Returns
        -------
        plotly.graph_objects.Figure
        """
        if x is None and y is None:
            raise ValueError("Either 'x' or 'y' must be given")
        data = self._data
        if orientation == 'auto':
            orientation = None
        if subplots:
            facet_row, facet_col, facet_col_wrap = subplots[0], subplots[1], subplots[2]
        else:
            facet_row, facet_col, facet_col_wrap = None, None, None
        if color:
            len_labels = data[color].nunique()
            nums = np.linspace(0, len_labels, len_labels) / len_labels
            color_discrete_sequence = [get_continuous_color(self._colorscale, z) for z in nums]
        else:
            color_discrete_sequence = None
        fig = px.box(data_frame=data,
                     x=x,
                     y=y,
                     color=color,
                     facet_row=facet_row,
                     facet_col=facet_col,
                     facet_col_wrap=facet_col_wrap,
                     boxmode=boxmode,
                     color_discrete_sequence=color_discrete_sequence,
                     points=points,
                     orientation=orientation,
                     **kwargs)
        if title == 'auto':
            if y and type(y) != list and pd.api.types.is_numeric_dtype(data[y]):
                title = f'Box Plot of {y}'
            elif x and type(x) != list and pd.api.types.is_numeric_dtype(data[x]):
                title = f'Box Plot of {x}'
            else:
                title = 'Box Plot'
        fig.update_layout(title=dict(text=title, x=0.5, xref='paper'),
                          margin=dict(l=0, r=0, t=50, b=0))
        fig.show()

    def scatter(self, x=None, y=None, sort=None, n=None, color=None, size=None, symbol=None, subplots=None, text=None,
                size_max=20, orientation='auto', opacity=1, edge=False, title='auto', slider=False, **kwargs):
        """
        Makes a scatter plot.

        Parameters
        ----------
        x: str or list of str, default=None
            Name of the column to draw on the x-axis. If it takes a list of
            column names, the input data is considered as wide-form
            rather than long-form.

        y: str or list of str, default=None
            Name of the column to draw on the y-axis. If it takes a list of
            column names, the input data is considered as wide-form
            rather than long-form.

        sort: str, default=None
            Name of the column to sort values by in descending (ascending)
            order if 'n' is positive (negative).

        n: int, default=None
            Number of sorted rows to draw. If positive, the rows are sorted in
            descending order; if negative, the rows are sorted in ascending order.

        color: str, default=None
            Name of the column used to set color to markers.

        size: str or int, default=None
            If str, it is a name of the column used to set marker sizes.
            If integer, it defines the marker size.

        symbol: str, default=None
            Name of the column used to set symbols to markers.

        subplots: (rows, cols, ncols), default=None
            Creates a set of subplots:
            - rows: name of the column to use for constructing subplots
              along the y-axis.
            - cols: name of the column to use for constructing subplots
              along the x-axis.
            - ncols: number of columns of the subplot grid.

        text: str, default=None
            Name of the column to use as text labels in the figure.

        size_max: int, default=20
            The maximum marker size. Used if 'size' is given.

        orientation: {'auto', 'v', 'h'}, default='auto'
            Orientation of the graph: 'v' for vertical and 'h' for horizontal.
            By default, it is determined automatically based on the input
            data types.

        opacity: float, default=1
            Opacity of the markers. Ranges from 0 to 1.

        edge: bool, default=False
            Whether to draw marker edges.

        title: str, default='auto'
            Title of the graph. When 'auto', the title is generated automatically.

        slider: bool, default=False
            Whether to add a range slider to the plot.

        **kwargs: optional
            See 'plotly.express.scatter' for other possible arguments.

        Returns
        -------
        plotly.graph_objects.Figure
        """
        if x is None and y is None:
            raise ValueError("Either 'x' or 'y' must be given")
        data = self._data
        if sort:
            if n > 0:
                data = data.sort_values(by=sort, ascending=False).head(n)
            elif n < 0:
                data = data.sort_values(by=sort, ascending=True).head(n)
        if pd.api.types.is_number(size):
            marker_size = size
            size = None
        else:
            marker_size = None
        if orientation == 'auto':
            orientation = None
        if subplots:
            facet_row, facet_col, facet_col_wrap = subplots[0], subplots[1], subplots[2]
        else:
            facet_row, facet_col, facet_col_wrap = None, None, None
        if color:
            len_labels = data[color].nunique()
            nums = np.linspace(0, len_labels, len_labels) / len_labels
            color_discrete_sequence = [get_continuous_color(self._colorscale, z) for z in nums]
        else:
            color_discrete_sequence = None
        fig = px.scatter(data_frame=data,
                         x=x,
                         y=y,
                         color=color,
                         symbol=symbol,
                         size=size,
                         text=text,
                         facet_row=facet_row,
                         facet_col=facet_col,
                         facet_col_wrap=facet_col_wrap,
                         color_discrete_sequence=color_discrete_sequence,
                         opacity=opacity,
                         size_max=size_max,
                         orientation=orientation,
                         **kwargs)
        if edge is True:
            fig.update_traces(marker=dict(line=dict(color='black', width=0.5)))
        if marker_size:
            fig.update_traces(marker_size=marker_size)
        if text:
            if pd.api.types.is_integer_dtype(data[text]):
                texttemplate = '%{text:.f}'
            else:
                texttemplate = '%{text:.2f}'
            fig.update_traces(texttemplate=texttemplate,
                              textposition='middle right')
        if title == 'auto':
            if y and type(y) != list and pd.api.types.is_numeric_dtype(data[y]):
                title = f'Scatter Plot of {y}'
            elif x and type(x) != list and pd.api.types.is_numeric_dtype(data[x]):
                title = f'Scatter Plot of {x}'
            else:
                title = 'Scatter Plot'
        if (y and type(y) != list and pd.api.types.is_numeric_dtype(data[y])) or (
                y and type(y) == list and pd.api.types.is_numeric_dtype(data[y[0]])):
            autorange = True
        else:
            autorange = 'reversed'
        if type(x) == list or type(y) == list:
            legend = dict(orientation='h', x=0.5, xanchor='center', y=1.01, yanchor='bottom', title=None)
            margin = dict(l=0, r=0, t=80, b=0)
        else:
            legend = {}
            margin = dict(l=0, r=0, t=50, b=0)
        fig.update_layout(title=dict(text=title, x=0.5, xref='paper'),
                          legend=legend,
                          margin=margin,
                          yaxis_autorange=autorange)
        if slider is True:
            fig.update_xaxes(rangeslider_visible=True)
        fig.show()

    def line(self, x=None, y=None, sort=None, n=None, color=None, group=None, dash=None, subplots=None, text=None,
             orientation='auto', line_width=2, title='auto', slider=False, **kwargs):
        """
        Makes a line plot.

        Parameters
        ----------
        x: str or list of str, default=None
            Name of the column to draw on the x-axis. If it takes a list of
            column names, the input data is considered as wide-form
            rather than long-form.

        y: str or list of str, default=None
            Name of the column to draw on the y-axis. If it takes a list of
            column names, the input data is considered as wide-form
            rather than long-form.

        sort: str, default=None
            Name of the column to sort values by in descending (ascending)
            order if 'n' is positive (negative).

        n: int, default=None
            Number of sorted rows to draw. If positive, the rows are sorted in
            descending order; if negative, the rows are sorted in ascending order.

        color: str, default=None
            Name of the column used to set color to lines.

        group: str, default=None
            Name of the column used to group data rows into lines.

        dash: str, default=None
            Name of the column used to set dash patterns to lines.

        subplots: (rows, cols, ncols), default=None
            Creates a set of subplots:
            - rows: name of the column to use for constructing subplots
              along the y-axis.
            - cols: name of the column to use for constructing subplots
              along the x-axis.
            - ncols: number of columns of the subplot grid.

        text: str, default=None
            Name of the column to use as text labels in the figure.

        orientation: {'auto', 'v', 'h'}, default='auto'
            Orientation of the graph: 'v' for vertical and 'h' for horizontal.
            By default, it is determined automatically based on the input
            data types.

        line_width: int, default=2
            Width of the line(s).

        title: str, default='auto'
            Title of the graph. When 'auto', the title is generated automatically.

        slider: bool, default=False
            Whether to add a range slider to the plot.

        **kwargs: optional
            See 'plotly.express.line' for other possible arguments.

        Returns
        -------
        plotly.graph_objects.Figure
        """
        if x is None and y is None:
            raise ValueError("Either 'x' or 'y' must be given")
        data = self._data
        if sort:
            if n > 0:
                data = data.sort_values(by=sort, ascending=False).head(n)
            elif n < 0:
                data = data.sort_values(by=sort, ascending=True).head(n)
        if orientation == 'auto':
            orientation = None
        if subplots:
            facet_row, facet_col, facet_col_wrap = subplots[0], subplots[1], subplots[2]
        else:
            facet_row, facet_col, facet_col_wrap = None, None, None
        if color:
            len_labels = data[color].nunique()
            nums = np.linspace(0, len_labels, len_labels) / len_labels
            color_discrete_sequence = [get_continuous_color(self._colorscale, z) for z in nums]
        else:
            color_discrete_sequence = None
        fig = px.line(data_frame=data,
                      x=x,
                      y=y,
                      color=color,
                      line_group=group,
                      line_dash=dash,
                      text=text,
                      facet_row=facet_row,
                      facet_col=facet_col,
                      facet_col_wrap=facet_col_wrap,
                      color_discrete_sequence=color_discrete_sequence,
                      orientation=orientation,
                      **kwargs)
        fig.update_traces(line_width=line_width)
        if text:
            if pd.api.types.is_integer_dtype(data[text]):
                texttemplate = '%{text:.f}'
            else:
                texttemplate = '%{text:.2f}'
            fig.update_traces(texttemplate=texttemplate,
                              textposition='top right')
        if title == 'auto':
            if y and type(y) != list and pd.api.types.is_numeric_dtype(data[y]):
                title = f'Line Plot of {y}'
            elif x and type(x) != list and pd.api.types.is_numeric_dtype(data[x]):
                title = f'Line Plot of {x}'
            else:
                title = 'Line Plot'
        if (y and type(y) != list and pd.api.types.is_numeric_dtype(data[y])) or (
                y and type(y) == list and pd.api.types.is_numeric_dtype(data[y[0]])):
            autorange = True
        else:
            autorange = 'reversed'
        if type(x) == list or type(y) == list:
            legend = dict(orientation='h', x=0.5, xanchor='center', y=1.01, yanchor='bottom', title=None)
            margin = dict(l=0, r=0, t=80, b=0)
        else:
            legend = {}
            margin = dict(l=0, r=0, t=50, b=0)
        fig.update_layout(title=dict(text=title, x=0.5, xref='paper'),
                          legend=legend,
                          margin=margin,
                          yaxis_autorange=autorange)
        if slider is True:
            fig.update_xaxes(rangeslider_visible=True)
        fig.show()

    def pie(self, labels, values=None, color=None, n=None, remainder=True, text='percent', text_orientation='auto',
            hole=0.4, opacity=1, edge=True, title='auto', **kwargs):
        """
        Makes a pie chart.

        Parameters
        ----------
        labels: str
            Name of the column to use as labels for sectors.

        values: str, default=None
            Name of the column used to set values to sectors.

        color: str, default=None
            Name of the column used to set color to sectors.

        n: int, default=None
            Number of sorted rows to draw. If positive, the rows are sorted in
            descending order; if negative, the rows are sorted in ascending order.

        remainder: bool, default=True
            Whether to put the remaining values other than 'n' selected into
            a separate sector.

        text: {'percent', 'value'}, default='percent'
            Text information to display inside sectors.
            Can be either 'percent' or 'value'.

        text_orientation: {'auto', 'horizontal', 'radial', 'tangential'},
            default='auto'
            Orientation of text inside sectors.
            - If 'auto', text is oriented to be as big as possible in the middle
              of the sector.
            - If 'horizontal', text is oriented to be parallel with the bottom
              of the chart.
            - If 'radial', text is oriented along the radius of the sector.
            - If 'tangential', text is oriented perpendicular to the radius
              of the sector.

        hole: float, default=0.4
            Fraction of the radius to cut out of the pie to create a donut chart.
            Ranges from 0 to 1.

        opacity: float, default=1
            Opacity of the sectors. Ranges from 0 to 1.

        edge: bool, default=True
            Whether to draw sector edges.

        title: str, default='auto'
            Title of the graph. When 'auto', the title is generated automatically.

        **kwargs: optional
            See 'plotly.express.pie' for other possible arguments.

        Returns
        -------
        plotly.graph_objects.Figure
        """
        data = self._data
        labels_input = labels
        values_input = values
        if not values:
            data = data[labels].value_counts()
            data_copy = data.copy()
            if n and n > 0:
                data = data.head(n)
                if remainder:
                    if data_copy[n:].sum() > 0:
                        data['Other'] = data_copy[n:].sum()
            elif n and n < 0:
                data = data.tail(-n)
                if remainder:
                    if data_copy[:-n].sum() > 0:
                        data['Other'] = data_copy[:-n].sum()
            data = pd.DataFrame(data).reset_index()
            values = labels
            labels = 'index'
            if text == 'percent':
                hovertemplate = values + '=%{label}<br>count=%{value}'
            else:  # text == 'value'
                hovertemplate = values + '=%{label}<br>percent=%{percent}'
        else:
            if n:
                data = data.sort_values(by=values, ascending=False).set_index(labels)[values]
                data_copy = data.copy()
                if n > 0:
                    data = data.head(n)
                    if remainder:
                        if data_copy[n:].sum() > 0:
                            data['Other'] = data_copy[n:].sum()
                elif n < 0:
                    data = data.tail(-n)
                    if remainder:
                        if data_copy[:-n].sum() > 0:
                            data['Other'] = data_copy[:-n].sum()
            data = pd.DataFrame(data).reset_index()
        len_labels = data[labels].nunique()
        nums = np.linspace(0, len_labels, len_labels) / len_labels
        color_discrete_sequence = [get_continuous_color(self._colorscale, z) for z in nums]
        fig = px.pie(data_frame=data,
                     names=labels,
                     values=values,
                     color=color,
                     color_discrete_sequence=color_discrete_sequence,
                     opacity=opacity,
                     hole=hole,
                     **kwargs)
        fig.update_traces(sort=False,
                          textinfo=text,
                          insidetextorientation=text_orientation)
        if edge is True:
            fig.update_traces(marker=dict(line=dict(color='white', width=1)))
        if not values_input:
            fig.update_traces(hovertemplate=hovertemplate)
        if title == 'auto':
            title = f'Pie Chart of {labels_input}'
        fig.update_layout(title=dict(text=title, x=0.5, xref='paper'),
                          legend=dict(title=labels_input),
                          margin=dict(l=0, r=0, t=50, b=0))
        fig.show()

    def sunburst(self, path, values=None, color=None, maxdepth=-1, text_orientation='auto', title='auto', **kwargs):
        """
        Makes a sunburst plot.

        Parameters
        ----------
        path: list of str
            Names of the columns that correspond to different levels of
            the hierarchy of sectors, from root to leaves.

        values: str, default=None
            Name of the column used to set values to sectors.

        color: str, default=None
            Name of the column used to set color to sectors.

        maxdepth: int, default=-1
            Number of displayed sectors from any level. If -1, all levels
            in the hierarchy are shown.

        text_orientation: {'auto', 'horizontal', 'radial', 'tangential'},
            default='auto'
            Orientation of text inside sectors.
            - If 'auto', text is oriented to be as big as possible in the middle
              of the sector.
            - If 'horizontal', text is oriented to be parallel with the bottom
              of the chart.
            - If 'radial', text is oriented along the radius of the sector.
            - If 'tangential', text is oriented perpendicular to the radius
              of the sector.

        title: str, default='auto'
            Title of the graph. When 'auto', the title is generated automatically.

        **kwargs: optional
            See 'plotly.express.sunburst' for other possible arguments.

        Returns
        -------
        plotly.graph_objects.Figure
        """
        data = self._data
        len_labels = data[path[0]].nunique()
        nums = np.linspace(0, len_labels, len_labels) / len_labels
        color_discrete_sequence = [get_continuous_color(self._colorscale, z) for z in nums]
        fig = px.sunburst(data_frame=data,
                          path=path,
                          values=values,
                          color=color,
                          color_discrete_sequence=color_discrete_sequence,
                          maxdepth=maxdepth,
                          **kwargs)
        fig.update_traces(insidetextorientation=text_orientation)
        if title == 'auto':
            title = f'Sunburst Plot of {path[0]}'
        fig.update_layout(title=dict(text=title, x=0.5, xref='paper'),
                          margin=dict(l=0, r=0, t=50, b=0))
        fig.show()

    def heatmap(self, x=None, y=None, color=None, subplots=None, nbins=None, agg=None, orientation='auto',
                title='auto', **kwargs):
        """
        Makes a density heatmap.

        Parameters
        ----------
        x: str or list of str, default=None
            Name of the column to draw on the x-axis. If it takes a list of
            column names, the input data is considered as wide-form
            rather than long-form.

        y: str or list of str, default=None
            Name of the column to draw on the y-axis. If it takes a list of
            column names, the input data is considered as wide-form
            rather than long-form.

        color: str, default=None
            Name of the column to aggregate and set color to blocks.

        subplots: (rows, cols, ncols), default=None
            Creates a set of subplots:
            - rows: name of the column to use for constructing subplots
              along the y-axis.
            - cols: name of the column to use for constructing subplots
              along the x-axis.
            - ncols: number of columns of the subplot grid.

        nbins: (nbinsx, nbinsy), default=None
            Number of bins along the x-axis and y-axis.

        agg: {'count', 'sum', 'avg', 'min', 'max'}, default=None
            Name of the function used to aggregate values of 'color'.

        orientation: {'auto', 'v', 'h'}, default='auto'
            Orientation of the graph: 'v' for vertical and 'h' for horizontal.
            By default, it is determined automatically based on the input
            data types.

        title: str, default='auto'
            Title of the graph. When 'auto', the title is generated automatically.

        **kwargs: optional
            See 'plotly.express.density_heatmap' for other possible arguments.

        Returns
        -------
        plotly.graph_objects.Figure
        """
        if x is None and y is None:
            raise ValueError("Either 'x' or 'y' must be given")
        data = self._data
        if orientation == 'auto':
            orientation = None
        if subplots:
            facet_row, facet_col, facet_col_wrap = subplots[0], subplots[1], subplots[2]
        else:
            facet_row, facet_col, facet_col_wrap = None, None, None
        if nbins:
            nbinsx, nbinsy = nbins[0], nbins[1]
        else:
            nbinsx, nbinsy = None, None
        fig = px.density_heatmap(data_frame=data,
                                 x=x,
                                 y=y,
                                 z=color,
                                 facet_row=facet_row,
                                 facet_col=facet_col,
                                 facet_col_wrap=facet_col_wrap,
                                 nbinsx=nbinsx,
                                 nbinsy=nbinsy,
                                 orientation=orientation,
                                 histfunc=agg,
                                 **kwargs)
        if title == 'auto':
            if x and y:
                title = f'2D Heat Map of {x} and {y}'
            elif x:
                title = f'2D Heat Map of {x}'
            elif y:
                title = f'2D Heat Map of {y}'
            else:
                title = '2D Heat Map'
        fig.update_layout(title=dict(text=title, x=0.5, xref='paper'),
                          margin=dict(l=0, r=0, t=50, b=0))
        fig.show()

    def gantt(self, x_start, x_end, y=None, color=None, subplots=None, text=None, opacity=1, title='auto', **kwargs):
        """
        Makes a Gantt chart.

        Parameters
        ----------
        x_start: str
            Name of the start date column to draw on the x-axis.

        x_end: str
            Name of the end date column to draw on the x-axis.

        y: str, default=None
            Name of the task column to draw on the y-axis.

        color: str, default=None
            Name of the column used to set color to bars.

        subplots: (rows, cols, ncols), default=None
            Creates a set of subplots:
            - rows: name of the column to use for constructing subplots
              along the y-axis.
            - cols: name of the column to use for constructing subplots
              along the x-axis.
            - ncols: number of columns of the subplot grid.

        text: str, default=None
            Name of the column to use as text labels in the figure.

        opacity: float, default=1
            Opacity of the bars. Ranges from 0 to 1.

        title: str, default='auto'
            Title of the graph. When 'auto', the title is generated automatically.

        **kwargs: optional
            See 'plotly.express.timeline' for other possible arguments.

        Returns
        -------
        plotly.graph_objects.Figure
        """
        data = self._data
        if subplots:
            facet_row, facet_col, facet_col_wrap = subplots[0], subplots[1], subplots[2]
        else:
            facet_row, facet_col, facet_col_wrap = None, None, None
        if color:
            len_labels = data[color].nunique()
            nums = np.linspace(0, len_labels, len_labels) / len_labels
            color_discrete_sequence = [get_continuous_color(self._colorscale, z) for z in nums]
        else:
            color_discrete_sequence = None
        fig = px.timeline(data_frame=data,
                          x_start=x_start,
                          x_end=x_end,
                          y=y,
                          color=color,
                          facet_row=facet_row,
                          facet_col=facet_col,
                          facet_col_wrap=facet_col_wrap,
                          color_discrete_sequence=color_discrete_sequence,
                          text=text,
                          opacity=opacity,
                          **kwargs)
        if text:
            if pd.api.types.is_integer_dtype(data[text]):
                texttemplate = '%{text:.f}'
            else:
                texttemplate = '%{text:.2f}'
            fig.update_traces(texttemplate=texttemplate,
                              textposition='auto')  # ['inside', 'outside', 'auto', 'none']
        if title == 'auto':
            title = f'Gantt Chart'
        fig.update_layout(title=dict(text=title, x=0.5, xref='paper'),
                          margin=dict(l=0, r=0, t=50, b=0),
                          yaxis_autorange='reversed')
        fig.show()

    def pareto(self, x, bins='auto', text=False, opacity=0.8, edge=False, title='auto'):
        """
        Makes a Pareto chart.

        Parameters
        ----------
        x: str
            Name of the column to make graph for.

        bins: list of int or 'auto', default='auto'
            List of the x coordinates of the bars. If 'auto, bins are determined
            automatically.

        text: bool, default=False
            Whether to show text labels in the figure.

        opacity: float, default=0.8
            Opacity of the bars. Ranges from 0 to 1.

        edge: bool, default=False
            Whether to draw bar edges.

        title: str, default='auto'
            Title of the graph. When 'auto', the title is generated automatically.

        Returns
        -------
        plotly.graph_objects.Figure
        """
        if pd.api.types.is_numeric_dtype(self._data[x]):
            if bins == 'auto':
                bins = np.arange(self._data[x].max() + 1)
            data = pd.cut(x=self._data[x], bins=bins, right=False).value_counts().sort_index()
            labels = bins  # [str(i) for i in data.index]
        else:
            data = self._data[x].value_counts()
            labels = data.index
        values = data.values
        shares = np.cumsum(data / data.sum()).values * 100
        nums = np.linspace(0, len(labels), len(labels)) / len(labels)
        cols = [get_continuous_color(self._colorscale, z) for z in nums]
        if edge:
            line = dict(color='black', width=0.6)
        else:
            line = dict()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=labels,
                             y=values,
                             marker=dict(color=cols, line=line),
                             opacity=opacity,
                             name='Frequency',
                             text=values))
        fig.add_trace(go.Scatter(x=labels,
                                 y=shares,
                                 yaxis='y2',
                                 name='Cumulative Percentage',
                                 mode='lines',
                                 marker=dict(color=px.colors.qualitative.Plotly[0]),
                                 line=dict(width=3)))
        if text is True:
            fig.update_traces(texttemplate='%{text:.0f}',
                              textposition='outside',
                              selector=dict(type='bar'))
        fig.update_traces(hovertemplate='%{y}',
                          selector=dict(type='bar'))
        fig.update_traces(hovertemplate='%{y:.2f}%',
                          selector=dict(type='scatter'))
        if title == 'auto':
            title = f'Pareto Chart of {x}'
        fig.update_layout(title=dict(text=title, x=0.5, xref='paper'),
                          yaxis=dict(title='Frequency'),
                          xaxis=dict(title=x),
                          hovermode='x',
                          legend=dict(orientation='h', x=0.5, xanchor='center', y=1.01, yanchor='bottom'),
                          margin=dict(l=0, r=0, t=80, b=0),
                          yaxis2=dict(title='Cumulative Percentage', anchor='x', overlaying='y', side='right',
                                      showgrid=False,
                                      titlefont=dict(color=px.colors.qualitative.Plotly[0]),
                                      tickfont=dict(color=px.colors.qualitative.Plotly[0])))
        fig.show()
