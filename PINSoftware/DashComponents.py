"""
This file has all the custom dash components used for the app. Some of the
most important ones are the graphs so I will give a bit of explanation to them.

There are two types of graphs defined here - `FullRedrawGraph` and `ExtendableGraph`.
The difference being that only the ExtendableGraph can be extended without resending all the data.
Both graphs are created in a container with a title, controls and an interval. Both have
at least two switches, the "Show graph" and the "Update graph" buttons. When "Show graph" is
off the graph is not rendered and its "Update graph" button is disabled. The "Update graph"
toggles the interval, when it is enabled the interval runs, otherwise not. Each type uses the
interval differently but both use it to update. More on in their respective documentations.
"""

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import dash

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from PINSoftware.MachineState import MachineState


def SingleSwitch(id_, label, default=False):
    """
    This returns a dash component containing a single switch (a nice looking checkbox)
    (not a part of a Checklist) using bootstrap.

    `id` is the id of the Checkbox component inside.

    `label` is the label shown beside it.

    `default` is the default value of the switch.
    """
    return html.Div([
                        dbc.Checkbox(id=id_, className='custom-control-input', checked=default),
                        html.Label(label, htmlFor=id_, className='custom-control-label'),
                    ],
                    className='custom-control custom-switch ml-2',
                    style=dict(display='inline')
                )


def get_base_graph_callbacks(app : dash.Dash, name : str):
    """
    This adds the most basic callbacks to a graph. It takes car of two things.
    Disabling the interval when the "Update graph" switch is off and disabling the
    "Update graph" when the "Show graph" button is off.
    """
    @app.callback([
            Output(name + '-row', 'style'),
            Output(name + '-clock-toggle', 'disabled'),
            Output(name + '-clock-toggle', 'checked'),
        ], [Input(name + '-show', 'checked')], [State(name + '-clock-toggle', 'checked')])
    def disable_update_on_show(show_checked, update_checked):
        if not show_checked:
            return [{'display': 'none'}, True, False]
        else:
            return [{}, False, update_checked]
    @app.callback(Output(name + '-clock', 'disabled'), [Input(name + '-clock-toggle', 'checked')])
    def toggle_interval(checked):
        return not checked

base_graph_callbacks_done = []

def BaseGraph(app : dash.Dash, name : str, title : str, interval : int = 2000, additional_controls=[], base_fig={}):
    """
    This creates a dash component with the most basic stuff for an updating graph.
    It sets up the container, the controls and the `dash_core_components.Interval`.
    It also sets up the basic callbacks using `get_base_graph_callbacks`.

    `app` is the app to add the callbacks to.
    
    `name` is the `dash_core_components.Graph` component id.

    `title` is the title of the graph, shown at the top of the container.

    `interval` is the `dash_core_components.Interval` interval in milliseconds.

    `additional_controls` is a list of dash components with should be added in the container,
    this is useful when you want to add additional controls to the graph.

    `base_fig` is what to set the `figure` property of the `dash_core_components.Graph` (it can be changed later though).
    """
    if name not in base_graph_callbacks_done:
        get_base_graph_callbacks(app, name)
        base_graph_callbacks_done.append(name)
    return dbc.Container([
            dbc.Row(html.H4(title), justify='center', className='mt-1'),
            dbc.Row([
                    SingleSwitch(name + '-show', "Show graph", default=True),
                    SingleSwitch(name + '-clock-toggle', "Update graph", default=True)
                ],
                justify='center',
                className='mt-1')
        ] + additional_controls + [
            dbc.Row(dbc.Col([
                dcc.Graph(
                    id=name,
                    config={'displayModeBar': True},
                    animate=False,
                    figure=base_fig
                    ),
                dcc.Interval(id=name + '-clock', interval=interval, n_intervals=0)
            ]),
            id=name + '-row',
            justify='center')
        ],
        id=name + '-container',
        className='border mt-3 mb-3 pb-2'
    )


def get_full_redraw_graph_callbacks(app : dash.Dash, ms : MachineState, name : str, fig_func, **kwargs):
    """
    Adds callbacks to a `FullRedrawGraph`. Specifically, whenever the `dash_core_components.Interval`
    triggers, if there is `ms.data` then the `figure_func` is called and its result is set as the new figure.

    `app` the dash app to add the callbacks to.

    If `fig_func_output` is a keyword argument, then its value is set as the output of the interval
    trigger callback (this is the one where `fig_func` is used).

    If `fig_func_state` is a keyword argument, then its value is set as the state of the interval
    trigger callback (this is the one where `fig_func` is used).

    The only thing that is fixed is the callback inputs.
    """
    fig_func_output = kwargs.setdefault('fig_func_output', Output(name, 'figure'))
    fig_func_state = kwargs.setdefault('fig_func_state', [])

    @app.callback(fig_func_output, [Input(name + '-clock', 'n_intervals')], fig_func_state)
    def graph_update(n, *args):
        if not ms.data:
            raise PreventUpdate()
        return fig_func(n,  *args)

full_redraw_graph_callbacks_done = []

def FullRedrawGraph(app : dash.Dash, ms : MachineState, name : str, title : str, fig_func,
        interval : int = 2000, additional_controls=[], **kwargs):
    """
    Get a graph which whenever it is updated, the whole figure is changed and passed over the network.

    `app` the dash app to add the callbacks to.

    `ms` the `PINSoftware.MachineState.MachineState` to use for checking for data.

    `name` is the `dash_core_components.Graph` component id.

    `title` is the title of the graph, shown at the top of the container.

    `fig_func` is the function to call on update. It is only called when `ms.data` is not None.
    Its output is the graph figure by default but can be changed using the `fig_func_output` keyword
    argument. It can also get more arguments, the callback state can be changed by the `fig_func_state`
    keyword argument.

    `interval` is the `dash_core_components.Interval` interval in milliseconds.

    `additional_controls` is a list of dash components with should be added in the container,
    this is useful when you want to add additional controls to the graph.
    """
    if name not in full_redraw_graph_callbacks_done:
        get_full_redraw_graph_callbacks(app, ms, name, fig_func, **kwargs)
        full_redraw_graph_callbacks_done.append(name)
    return BaseGraph(app, name, title, interval, additional_controls)


def get_extendable_graph_callbacks(app : dash.Dash, ms : MachineState, name : str, extend_func,
        base_fig, **kwargs):
    """
    Adds callbacks to a `ExtendableGraph`. It adds two callbacks, Firstly, whenever
    the "Stop" button is enabled, the graphs figure is set to `base_fig`. The second one is
    that whenever the interval triggers, the graph is extended using `extend_func`.

    `app` the dash app to add the callbacks to.

    If `extend_func_output` is a keyword argument, then its value is set as the output of the callback
    using `extend_func` (the interval one). The default is the graph 'extendData'.

    If `extend_func_state` is a keyword argument, then its value is set as the state of the callback
    using `extend_func` (the interval one). The default is an empty list.

    The only thing that is fixed is the callback inputs.
    """
    extend_func_output = kwargs.setdefault('extend_func_output', Output(name, 'extendData'))
    extend_func_state = kwargs.setdefault('extend_func_state', [])

    @app.callback(Output(name, 'figure'), [
            Input('cp-stop', 'disabled')
        ])
    def set_base_fig(is_unstoppable):
        if not is_unstoppable:
            return base_fig
        else:
            raise PreventUpdate()
    @app.callback(extend_func_output, [Input(name + '-clock', 'n_intervals')], extend_func_state)
    def graph_update(n, *args):
        if not ms.data:
            raise PreventUpdate()
        return extend_func(n, *args)

extendable_graph_callbacks_done = []

def ExtendableGraph(app : dash.Dash, ms : MachineState, name : str, title : str,
        base_fig, extend_func, interval : int = 2000, additional_controls=[], **kwargs):
    """
    Get a graph to which new data is added instead of redrawing it completely. Its figure
    is first set to `base_fig` and is then updated using `extend_func`

    `app` the dash app to add the callbacks to.

    `ms` the `PINSoftware.MachineState.MachineState` to use for checking for data.

    `name` is the `dash_core_components.Graph` component id.

    `title` is the title of the graph, shown at the top of the container.

    `base_fig` is the basic figure. This is what the figure property of the `dash_core_components.Graph`
    is set to when the page loads and whenever the "Stop" button becomes enabled (this is to reset when the
    next acquisition starts) (however this means that it will not reset on new data acquisition for users who
    are not controlling the setup at that point! Just keep that in mind).

    `extend_func` is the function to call on 'update', this is whenever the interval triggers. Its output
    is what is sent to the `dash_core_components.Graph`s `extendData` property by default but can be
    changed using the `extend_func_output` keyword argument.  It can also get more arguments, the callback
    state can be changed by the `extend_func_state` keyword argument.

    `interval` is the `dash_core_components.Interval` interval in milliseconds.

    `additional_controls` is a list of dash components with should be added in the container,
    this is useful when you want to add additional controls to the graph.
    """
    if name not in extendable_graph_callbacks_done:
        get_extendable_graph_callbacks(app, ms, name, extend_func, base_fig, **kwargs)
        extendable_graph_callbacks_done.append(name)
    return BaseGraph(app, name, title, interval, additional_controls, base_fig=base_fig)
