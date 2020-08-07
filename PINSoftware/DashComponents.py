import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


def SingleSwitch(id_, label, default=False):
    return html.Div([
                        dbc.Checkbox(id=id_, className='custom-control-input', checked=default),
                        html.Label(label, htmlFor=id_, className='custom-control-label'),
                    ],
                    className='custom-control custom-switch ml-2',
                    style=dict(display='inline')
                )


def get_base_graph_callbacks(app, ms, name):
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

def BaseGraph(app, ms, name, title, interval=2000, additional_controls=[]):
    if name not in base_graph_callbacks_done:
        get_base_graph_callbacks(app, ms, name)
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
                    animate=False
                    ),
                dcc.Interval(id=name + '-clock', interval=interval, n_intervals=0)
            ]),
            id=name + '-row',
            justify='center')
        ],
        id=name + '-container',
        className='border mt-3 mb-3 pb-2'
    )


def get_full_redraw_graph_callbacks(app, ms, name, fig_func, **kwargs):
    fig_func_output = kwargs.setdefault('fig_func_output', Output(name, 'figure'))
    fig_func_state = kwargs.setdefault('fig_func_state', [])

    @app.callback(fig_func_output, [Input(name + '-clock', 'n_intervals')], fig_func_state)
    def graph_update(n, *args):
        if not ms.data:
            raise PreventUpdate()
        return fig_func(n,  *args)

full_redraw_graph_callbacks_done = []

def FullRedrawGraph(app, ms, name, title, fig_func, interval=2000, additional_controls=[], **kwargs):
    if name not in full_redraw_graph_callbacks_done:
        get_full_redraw_graph_callbacks(app, ms, name, fig_func, **kwargs)
        full_redraw_graph_callbacks_done.append(name)
    return BaseGraph(app, ms, name, title, interval, additional_controls)


def get_extendable_graph_callbacks(app, ms, name, extend_func, base_fig_func, **kwargs):
    base_fig_func_output = kwargs.setdefault('base_fig_func_output', Output(name, 'figure'))
    base_fig_func_state = kwargs.setdefault('base_fig_func_state', [])
    extend_func_output = kwargs.setdefault('extend_func_output', Output(name, 'extendData'))
    extend_func_state = kwargs.setdefault('extend_func_state', [])

    @app.callback(base_fig_func_output, [Input('ut-on_load', 'children'), Input('cp-stop', 'disabled')], base_fig_func_state)
    def set_base_fig(not_used, is_unstoppable, *args):
        if not is_unstoppable:
            return base_fig_func(*args)
        else:
            raise PreventUpdate()
    @app.callback(extend_func_output, [Input(name + '-clock', 'n_intervals')], extend_func_state)
    def graph_update(n, *args):
        if not ms.data:
            raise PreventUpdate()
        return extend_func(n, *args)

extendable_graph_callbacks_done = []

def ExtendableGraph(app, ms, name, title, base_fig_func, extend_func, interval=2000, additional_controls=[], **kwargs):
    if name not in extendable_graph_callbacks_done:
        get_extendable_graph_callbacks(app, ms, name, extend_func, base_fig_func, **kwargs)
        extendable_graph_callbacks_done.append(name)
    return BaseGraph(app, ms, name, title, interval, additional_controls)
