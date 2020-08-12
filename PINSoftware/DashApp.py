import base64
import datetime
import os
import uuid
import urllib

from PINSoftware.MachineState import MachineState
from PINSoftware.DashComponents import FullRedrawGraph, ExtendableGraph, SingleSwitch
from PINSoftware.DataSaver import Filetype

import flask
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


def linear_correct_func(cor_a, cor_b):
    """Get a linear function with `a` and `b` as its coefficients"""
    return lambda x: cor_a * x + cor_b


def get_app(ms : MachineState) -> dash.Dash:
    """
        Creates the Dash app and creates all the callbacks.
        `ms` is the MachineState instance to which callbacks should be connected.
        Returns a `dash.Dash` instance to be run.
    """
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.config.suppress_callback_exceptions = False
    app.logger.disabled = False

    def timestamp_to_datetime(x : int) -> datetime.datetime:
        """Converts the timestamps sotred in `PINSoftware.DataAnalyser.DataAnalyser` to a `datetime.datetime` object"""
        return datetime.datetime.fromtimestamp(ms.data.first_processed_timestamp + x * ms.data.period)

    full_graph_base_fig = {'data': [
            {
                'x': [],
                'y': [],
                'type': 'scatter',
                'name': 'Live peak voltage'
            },
            {
                'x': [],
                'y': [],
                'type': 'scatter',
                'name': 'Live averaged peak voltage'
            }
        ]
    }

    def full_graph_extend(n, graph_indices):
        """Full graph extend function"""
        pro_index = min(graph_indices['pro_index'], len(ms.data.processed_ys))
        avg_index = min(graph_indices['avg_index'], len(ms.data.averaged_processed_ys))
        pro_top_index = min(pro_index + 30000, len(ms.data.processed_ys))
        avg_top_index = min(avg_index + 30000, len(ms.data.averaged_processed_ys))
        result = [
                {
                    'x': [
                        list(map(timestamp_to_datetime, ms.data.processed_timestamps[pro_index:pro_top_index])),
                        list(map(timestamp_to_datetime, ms.data.averaged_processed_timestamps[avg_index:avg_top_index]))
                    ],
                    'y': [
                        ms.data.processed_ys[pro_index:pro_top_index],
                        ms.data.averaged_processed_ys[avg_index:avg_top_index]
                        ]
                }
            ]
        graph_indices['pro_index'] = pro_top_index
        graph_indices['avg_index'] = avg_top_index
        return [result, graph_indices]

    def live_graph_func(n, T):
        """Live graph figure function"""
        show_from = len(ms.data.ys) - T * 50000
        data = []
        current_avg = None
        current_count = None
        if ms.data.processed_ys and ms.data.processed_timestamps[-1] >= show_from:
            pro_index = -1
            max_pro_index = -len(ms.data.processed_timestamps)
            while ms.data.processed_timestamps[pro_index] > show_from and pro_index > max_pro_index:
                pro_index -= 1
            data.append(
                {
                    'x': list(map(timestamp_to_datetime, ms.data.processed_timestamps[pro_index:])),
                    'y': ms.data.processed_ys[pro_index:],
                    'type': 'scatter',
                    'name': 'Live averaged peak voltage'
                }
            )
            current_count = -pro_index / T
        if ms.data.averaged_processed_ys and ms.data.averaged_processed_timestamps[-1] >= show_from:
            avg_index = -1
            max_avg_index = -len(ms.data.averaged_processed_timestamps)
            while ms.data.averaged_processed_timestamps[avg_index] > show_from and avg_index > max_avg_index:
                avg_index -= 1
            data.append(
                {
                    'x': list(map(timestamp_to_datetime, ms.data.averaged_processed_timestamps[avg_index:])),
                    'y': ms.data.averaged_processed_ys[avg_index:],
                    'type': 'scatter',
                    'name': 'Live peak voltage'
                }
            )
            current_avg = sum(ms.data.averaged_processed_ys[avg_index:]) / -avg_index
        return [{'data': data},
                "The average value is: " + str(current_avg) if current_avg else "",
                "Current peak voltages per second are: " + str(current_count) if current_avg else ""
                ]

    app.layout = lambda: dbc.Container([
        html.H1("xPIN, Sample and Hold, NI-DAQmx system software", style={'textAlign': 'center'}),
        dbc.Modal([
                dbc.ModalHeader("Warning"),
                dbc.ModalBody("Something went wrong", id='warning-modal-body')
            ],
            id='warning-modal'
        ),
        dbc.Container([
            dbc.Tabs([
                dbc.Tab(dbc.Container([
                    dbc.Row(
                        dbc.Col(
                            id='ad-session_id',
                            width='auto'
                        ),
                        justify='center'
                    ),
                    dbc.Row(
                        dbc.Col(
                            dbc.ButtonGroup([
                                dbc.Button("Grab control", id='ad-grab', color='warning', disabled=ms.experiment_running),
                                dbc.Button("Release control", id='ad-release', color='secondary', disabled=(not ms.experiment_running))
                            ]),
                            width='auto'
                        ),
                        justify='center'
                    ),
                    dbc.Row(
                        dbc.Col(
                            "There is currently no controller.",
                            id='ad-controller-info',
                            width='auto'
                        ),
                        justify='center'
                    )],
                    className='mt-3 mb-3'
                ), label="Administration", tab_id='administration-tab'),
                dbc.Tab(dbc.Container([
                    dbc.Row([
                        dbc.Col(
                            dbc.ButtonGroup([
                                dbc.Button("Start", id='cp-start', color='success', disabled=ms.experiment_running),
                                dbc.Button("Stop", id='cp-stop', color='danger', disabled=(not ms.experiment_running))
                            ]),
                            width='auto'
                        )],
                        justify='center',
                        className='mt-3 mb-2'
                    ),
                    dbc.Row(
                        dbc.Col(
                            html.Fieldset(dbc.Container([
                                dbc.Row(
                                    dbc.Col(
                                        SingleSwitch('cp-save-toggle', "Save captured data?", default=False),
                                        width='auto'
                                    ),
                                    justify='center'
                                ),
                                dbc.Row(
                                    dbc.Col(
                                        dbc.Input(id='cp-save-base_filename', value="log", type='text'),
                                        width='auto'
                                    ),
                                    id='cp-save-base_filename-row',
                                    justify='center'
                                ),
                                dbc.Row(
                                    dbc.Col(
                                        dbc.Select(
                                            id='cp-save-select_ft',
                                            value="hdf5",
                                            options=[
                                                {"label": "csv", "value": "csv"},
                                                {"label": "hdf5", "value": "hdf5"}
                                            ],
                                        ),
                                        width=2
                                    ),
                                    id='cp-save-select_ft-row',
                                    justify='center',
                                    className='mt-1'
                                ),
                                dbc.Row(
                                    dbc.Col(
                                        dbc.Checklist(
                                            id='cp-save-items',
                                            options=[
                                                {'label': "Save raw data", 'value': 'ys'},
                                                {'label': "Save processed data", 'value': 'processed_ys'},
                                                {'label': "Save averaged data", 'value': 'averaged_processed_ys'},
                                                {'label': "Save debug markers", 'value': 'markers'}
                                            ],
                                            value=['ys', 'processed_ys'],
                                            switch=True,
                                            inline=True
                                        ),
                                        width='auto'
                                    ),
                                    id='cp-save-items-row',
                                    justify='center'
                                ),
                                dbc.Row(
                                    dbc.Col(
                                        id='cp-save-messagebox',
                                        width='auto'
                                    ),
                                    justify='center'
                                )],
                                id='cp-saving-options',
                                fluid=True,
                                className='border mt-1 mb-1 pt-1 pb-2'
                            ), id='cp-saving-options-fieldset'),
                            width=8
                        ),
                        justify='center'
                    )]
                ), label="Run controls", id='run-options', tab_id='run-options-tab', disabled=True),
                dbc.Tab(dbc.Container([
                    dbc.Row(
                        dbc.Col(
                            html.Fieldset(dbc.Container([
                                    dbc.Row(
                                        dbc.Col(
                                            dbc.ButtonGroup([
                                                dcc.Upload(dbc.Button("Load configuration from file", color='info'),
                                                    id='cp-da-config_upload',
                                                    max_size=256*1024*1024),
                                                dcc.Link(
                                                    dbc.Button("Save configuration to file", color='secondary'),
                                                    id='cp-da-config_link',
                                                    href='',
                                                    refresh=True
                                                ),
                                            ]),
                                            width='auto'
                                        ),
                                        className='mt-2 mb-2',
                                        justify='center'
                                    ),
                                    dbc.Row(dbc.Col(dbc.FormGroup([
                                            dbc.Label("Edge detection threshold [V]:", html_for='cp-da-edge_detection_threshold', width='auto'),
                                            dbc.Col(
                                                dbc.Input(id='cp-da-edge_detection_threshold', type='number', min=0, value=0.005, step=0.0001),
                                                width=3
                                            )
                                        ],
                                        row=True
                                    ))),
                                    dbc.Row([
                                        dbc.Col(dbc.FormGroup([
                                                dbc.Label("Correction a", html_for='cp-da-correction_a', width='auto'),
                                                dbc.Col(
                                                    dbc.Input(id='cp-da-correction_a', type='number', value=2, step=0.01),
                                                    width=5
                                                )
                                            ],
                                            row=True
                                        )),
                                        dbc.Col(dbc.FormGroup([
                                                dbc.Label("Correction b", html_for='cp-da-correction_b', width='auto'),
                                                dbc.Col(
                                                    dbc.Input(id='cp-da-correction_b', type='number', value=0.0022, step=0.0001),
                                                    width=5
                                                )
                                            ],
                                            row=True
                                        ))
                                    ]),
                                    dbc.Row(dbc.Col(dbc.FormGroup([
                                            dbc.Label("Average count:", html_for='cp-da-average_count', width='auto'),
                                            dbc.Col(
                                                dbc.Input(id='cp-da-average_count', type='number', min=0, value=50, step=1),
                                                width=3
                                            )
                                        ],
                                        row=True
                                    ))),
                                ],
                                id='cp-dataanalyser-options',
                                fluid=True,
                                className='border mt-1 mb-1 pt-1 pb-2'
                            ), id='cp-dataanalyser-options-fieldset'),
                            width=10
                        ),
                        justify='center',
                        className='mt-3'
                    )]
                ), label="Processing controls", id='processing-options', tab_id='processing-options-tab', disabled=True),
                dbc.Tab(dbc.Container([
                    html.H3("System overview"),
                    html.P("""
                        The application is internally divided into two parts, the machine controls themselves and the user interface.
                        There are only one machine controls per server but there can be multiple user interfaces if multiple people open the website at once.
                        Because of this there is a 'user' system and only the current controller can control the machine controls.
                        When you open the website you are given a session id which can be seen at the top of the Administration tab and looks like this "9fb86f8a-51f5-40f0-b629-1f508a904e6a".
                        Under the session id there are two buttons, those are used to grab and release control of the machine.
                        Under those is the current controller info box, this shows if there is a controller and who it is.
                        If there is a controller which isn't you, you can force remove their control.
                        This has its problems but since the device is meant to be run in a controlled environment it should be good enough.
                    """),
                    html.P("""
                        Once you are the current controller you get access to two controls tabs.
                        In the Run controls tab you can start and stop data acquisition and choose how/if the data should be saved.
                        In the Processing controls tab you can modify parameters which are used during data analysis.
                    """),
                    html.H3("Notes on data analysis"),
                    html.P("""
                        The device processes the data by detecting sections and it then gets the differences between certain sections.
                        The Edge detection threshold parameter is the voltage difference which constitutes a section transition.
                        What is meant by that is that when the difference between the new datapoint and the average of the current section is greater than the EDT, then this is labeled as an edge and a new section begins.
                    """),
                    html.P("""
                        Peak voltage is a term which refers to the max voltage of the peak.
                        If there are a 1000 pulses per second then there should be a 1000 peak voltages per second.
                        Correction a and Correction b modify this value.
                        It has been observed that the sample and hold alters the voltages it gets, thereby this is necessary.
                        When the data analysis gets a new peak voltage it then multiplies that value by Correction a and adds Correction b to it.
                        The defaults have been calibrated for our setup using a signal generator and should be fine but you want to get raw data just set them to 1 and 0 respectively.
                    """),
                    html.P("""
                        Lastly, there are also the Averaged peak voltages, those are calculated from Peak voltages by averaging a set amount of them, this is done to reduce noise.
                        The Average count parameter sets how many peak voltages should be averaged.
                    """),
                    html.H3("Graph commentary"),
                    html.P("""
                        Both graphs have two options.
                        First is to show the graph and the second is to update it.
                        When both are on then the graph checks every 2 seconds for new data.
                        If you switch Update graph off, the graph will no longer update but will still be visible.
                        If you switch Update graph back on after a while it's still going to update every 2 seconds but it might not be able to catch up instantly, there is a set maximum datapoints that it can transfer not to overload the network.
                        When switch Show graph off, it automatically switches Update graph off too.
                        When you plan to let the acquisition run for a longer time it is strongly recommended to switch Show graph off for graphs of all data, otherwise they might cause issues.
                    """),
                    html.P("""
                        On the live graph there are two extra things.
                        First you can set how much data it will show and secondly, once it's running it will tell you how many Peak voltages it gets per second (in that interval).
                        The Peaks per second display can be very useful to find the right value for Edge detection threshold.
                    """)],
                    className='mt-3'
                ), label="Help", tab_id='help-tab')
            ], id='main-tabs')
        ]),
        dbc.Container(id='graphs', children=[
            ExtendableGraph(app, ms, 'full-graph', "All data from this measurement", full_graph_base_fig, full_graph_extend,
                extend_func_output=[Output('full-graph', 'extendData'), Output('full-graph-indices', 'data')],
                extend_func_state=[State('full-graph-indices', 'data')]),
            FullRedrawGraph(app, ms, 'live-graph', "Data from the last few seconds", live_graph_func,
                fig_func_output=[Output('live-graph', 'figure'), Output('live-graph-average', 'children'),
                    Output('live-graph-count', 'children')],
                fig_func_state=[State('live-graph-T', 'value')],
                additional_controls=[
                    dbc.Row([
                        dbc.Col(
                            dbc.FormGroup([
                                dbc.Label("How many seconds to look in the past:", html_for='live-graph-T', width='auto'),
                                    dbc.Col(
                                        dbc.Input(id='live-graph-T', type='number', min=0, value=5, step=0.01),
                                        width=4
                                    )
                                ],
                                row=True
                            ),
                            width='auto'
                        )],
                        justify='center'
                    ),
                    dbc.Row([
                        dbc.Col(
                            "",
                            id='live-graph-average',
                            width='auto'
                        )],
                        justify='center'
                    ),
                    dbc.Row([
                        dbc.Col(
                            "",
                            id='live-graph-count',
                            width='auto'
                        )],
                        justify='center'
                    )
                ])
        ]),
        dbc.Container(id='extras', className='mb-5', style={'display': 'none'}, children=[
            dcc.Store(id='session-id', storage_type='session'),
            dcc.Store(id='full-graph-indices', storage_type='session', data={'pro_index': 0, 'avg_index': 0}),
            html.Div(id='ut-on_load'),
            html.Div(id='ut-on_load-2'),
            html.Div(id='ut-update-controller-status'),
            html.Div(id='ut-update-controller-status-2'),
            html.Div(id='ut-update-controller-status-3'),
            html.Div(id='ut-update-controller-status-4'),
            html.Div(id='ut-show-warning-modal-0'),
            html.Div(id='ut-show-warning-modal-1'),
            html.Div(id='ut-show-warning-modal-2'),
            html.Div(id='ut-show-warning-modal-3')
        ])
    ])

    @app.callback([
            Output('ad-grab', 'n_clicks'),
            Output('session-id', 'data'),
            Output('ad-session_id', 'children'),
            Output('ut-update-controller-status', 'children')
        ], [Input('ut-on_load', 'children')], [State('session-id', 'data')])
    def on_load(not_used, old_sid):
        """Triggers on load"""
        if not old_sid:
            sid = str(uuid.uuid4())
            return [42, sid, sid, ""]
        return [42, old_sid, old_sid, ""]

    warning_modal_count = 4
    warning_modal_div_names = ['ut-show-warning-modal-' + str(i) for i in range(warning_modal_count)]
    warning_modal_prop_id_names = [warning_modal_div_name + '.children' for warning_modal_div_name in warning_modal_div_names]

    @app.callback([
            Output('warning-modal', 'is_open'),
            Output('warning-modal-body', 'children')
        ], [Input(warning_modal_div_name, 'children') for warning_modal_div_name in warning_modal_div_names])
    def show_warning_modal(*args):
        """
        This shows a modal with a warning whenever the children of one of the warning-modal divs
        change. It displays the contents of the div in the modal.
        """
        prop_id = dash.callback_context.triggered[0]['prop_id']
        try:
            children = args[warning_modal_prop_id_names.index(prop_id)]
            if children:
                return [True, children]
            else:
                raise PreventUpdate()
        except ValueError:
            raise PreventUpdate()

    @app.callback([
            Output('ad-grab', 'disabled'),
            Output('ad-release', 'disabled'),
            Output('run-options', 'disabled'),
            Output('processing-options', 'disabled'),
            Output('ad-controller-info', 'children'),
            Output('main-tabs', 'active_tab')
        ], [
            Input('ut-update-controller-status', 'children'),
            Input('ut-update-controller-status-2', 'children'),
            Input('ut-update-controller-status-3', 'children'),
            Input('ut-update-controller-status-4', 'children')
        ], [State('session-id', 'data'), State('main-tabs', 'active_tab')])
    def update_controller_status(not_used, not_used_2, not_used_3, not_used_4, sid, active):
        """Updates the current controller information box"""
        if not ms.controller:
            return [False, True, True, True, "There is currently no controller!", 'administration-tab']
        elif ms.controller == sid:
            return [True, False, False, False, "Tou are the current controller", active]
        else:
            infobox = [ms.controller + " is the current controller"]
            infobox.append(dbc.Button("Force release?", id='ad-force_release', color='danger', className='ml-3 mr-3'))
            return [True, True, True, True, infobox, 'administration-tab']

    @app.callback([
            Output('ut-update-controller-status-2', 'children'),
            Output('ut-show-warning-modal-1', 'children'),
        ], [Input('ad-grab', 'n_clicks'), Input('ad-release', 'n_clicks')], [State('session-id', 'data')])
    def grab_release(not_used, not_used_2, sid):
        """Handles the "Grab" and "Release" buttons"""
        prop_id = dash.callback_context.triggered[0]['prop_id']
        if prop_id.startswith('ad-grab'):
            if not ms.controller:
                ms.grab_control(sid)
                return ["", ""]
            else:
                return ["", "Sorry, someone has grabbed control before you have."]
        elif prop_id.startswith('ad-release'):
            if ms.controller == sid:
                ms.release_control()
                return ["", "You are now not in control of the system."]
            else:
                return ["", "Someone has removed your control before, you are now not the controller."]
        else:
            raise PreventUpdate()

    @app.callback([
            Output('ut-update-controller-status-3', 'children'),
            Output('ut-show-warning-modal-2', 'children')
        ], [
            Input('ad-force_release', 'n_clicks'),
        ], [
            State('ad-controller-info', 'children'),
            State('ut-show-warning-modal-2', 'children')
        ])
    def force_release(n_clicks, controller_info, warning_msg):
        """Handles the "Force Release" button"""
        if n_clicks:
            if ms.controller:
                if controller_info[0].startswith(ms.controller):
                    ms.release_control()
                    return ["", ""]
                else:
                    return ["", "Someone else has become the controller since last refresh."]
            else:
                return ["", ""]
        return ["", warning_msg]

    @app.callback(
            [
                Output('ut-show-warning-modal-0', 'children'),
                Output('cp-start', 'disabled'),
                Output('cp-stop', 'disabled'),
                Output('cp-saving-options-fieldset', 'disabled'),
                Output('cp-dataanalyser-options-fieldset', 'disabled'),
                Output('cp-save-messagebox', 'children'),
                Output('ut-update-controller-status-4', 'children')
            ],
            [
                Input('cp-start', 'n_clicks'),
                Input('cp-stop', 'n_clicks')
            ],
            [
                State('session-id', 'data'),
                State('cp-save-toggle', 'checked'),
                State('cp-save-base_filename', 'value'),
                State('cp-save-select_ft', 'value'),
                State('cp-save-items', 'value'),
                State('cp-da-edge_detection_threshold', 'value'),
                State('cp-da-average_count', 'value'),
                State('cp-da-correction_a', 'value'),
                State('cp-da-correction_b', 'value')
            ])
    def start_stop(start_ncl, stop_ncl, sid,
            should_save, save_filename, save_filetype, save_items,
            edge_detection_threshold, average_count, correction_a, correction_b):
        """
        Handles the "Start" and "Stop" buttons, this is the most complicated callback.

        First if the client isn't the current controller it disables the control tabs for him,
        updates his current controller info and shows a warning modal explaining what happened to him.

        Otherwise it splits based on if he pressed "Start" or "Stop".
        If he pressed "Start", it tries to start data acquisition and shows an info box
        telling the client if it worked, failed or what, it also disables one of the buttons.
        For "Stop" it just stops the data acquisition and shows a message with possibly a link to the data.
        """
        prop_id = dash.callback_context.triggered[0]['prop_id']
        if (start_ncl or stop_ncl) and sid != ms.controller:
            return ["Someone has forcefully removed your control of the system.", prop_id.startswith('cp-start'),
                    prop_id.startswith('cp-stop'), prop_id.startswith('cp-stop'), prop_id.startswith('cp-stop'), prop_id.startswith('cp-stop'), ""]
        out = []
        if prop_id.startswith('cp-start'):
            if should_save and (not save_filename.isalnum()):
                    return ["The supplied filename is not valid, aborting. The filename must only contain letters and numbers.",
                            False, True, False, False, "Aborted due to invalid filename", ""]
            ms.start_experiment(save_filename if should_save else None, Filetype.from_str(save_filetype),
                    edge_detection_threshold=edge_detection_threshold, average_count=average_count, items=save_items,
                    correction_func=linear_correct_func(correction_a, correction_b))
            if should_save:
                out = ["", True, False, True, True]
                if ms.saver:
                    out.append("Started acquiring and saving to file \"" + ms.saver.full_filename + "\"")
                elif should_save:
                    out.append("Acquiring has started but there has been an error with saving the data")
            else:
                out = ["", True, False, True, True, "Acquisition has started successfully"]
        elif prop_id.startswith('cp-stop'):
            ms.stop_experiment()
            msgbox = ["The Acquisition has been successfully stopped."]
            if ms.data:
                if ms.saver:
                    msgbox.append(html.A(
                        "Download the data here.",
                        href=ms.saver.full_filename[1:]
                    ))
            out = ["", False, True, False, False, msgbox]
        else:
            raise PreventUpdate()
        return out + [""]

    @app.callback([
            Output('cp-save-base_filename-row', 'style'),
            Output('cp-save-select_ft-row', 'style'),
            Output('cp-save-items-row', 'style')
        ],
        [
            Input('cp-save-toggle', 'checked'),
            Input('cp-save-select_ft', 'value')
        ])
    def cp_save_ui_callbacks(should_save, filetype):
        """This toggles visibility of the save options based on if saving is enabled"""
        out = [{}, {}, {}]
        if not should_save:
            out[0]['display']= 'none'
            out[1]['display']= 'none'
            out[2]['display']= 'none'
        if filetype != "hdf5":
            out[2]['display']= 'none'
        return out

    @app.callback([
            Output('cp-da-edge_detection_threshold', 'value'),
            Output('cp-da-correction_a', 'value'),
            Output('cp-da-correction_b', 'value'),
            Output('cp-da-average_count', 'value'),
            Output('ut-show-warning-modal-3', 'children'),
        ], [Input('cp-da-config_upload', 'contents')], [
            State('cp-da-edge_detection_threshold', 'value'),
            State('cp-da-correction_a', 'value'),
            State('cp-da-correction_b', 'value'),
            State('cp-da-average_count', 'value'),
        ])
    def upload_config(cont, edt, ca, cb, ac):
        """
        This handles the processing configuration uploading.

        It processes the file line by line, stripping each line. Then it tries
        to split it on the '=' character into exactly two parts. Then if the
        first part matches any of the property names, the second part is converted
        to the correct type and assigned as the property value.

        If anything goes wrong during it, then all of the values stay the same.
        """
        if not cont:
            raise PreventUpdate()
        old_edt = edt
        old_ca = ca
        old_cb = cb
        old_ac = ac
        try:
            for k, v in [map(lambda x: x.strip(), line.split('=')) for line in
                    base64.b64decode(cont.split(',')[1]).decode().strip().split('\n')]:
                if k == 'edge_detection_threshold':
                    edt = float(v)
                elif k == 'correction_a':
                    ca = float(v)
                elif k == 'correction_b':
                    cb = float(v)
                elif k == 'average_count':
                    ac = int(v)
                else:
                    ms.debugger.warning("Config loading: \"" + k + "\" does not match any of the parameter names.")
                    raise Exception()
            return [edt, ca, cb, ac, ""]
        except:
            return [old_edt, old_ca, old_cb, old_ac, "The uploaded file could not be parsed, try a different one."]

    @app.callback(Output('cp-da-config_link', 'href'), [
            Input('cp-da-edge_detection_threshold', 'value'),
            Input('cp-da-correction_a', 'value'),
            Input('cp-da-correction_b', 'value'),
            Input('cp-da-average_count', 'value'),
            Input('ut-on_load-2', 'children')
        ])
    def save_config(edt, ca, cb, ac, not_used):
        """Sets the href on the download link to the new value whenever the parameters change."""
        config = 'edge_detection_threshold=' + str(edt) + '\n' + 'correction_a=' + str(ca) + '\n' + 'correction_b=' + str(cb) + '\n' + 'average_count=' + str(ac) + '\n'
        return 'data:text/csv;charset=utf-8,' + urllib.parse.quote(config),

    @app.server.route('/logs/<path:path>')
    def get_log(path):
        """This enables downloading logs, whenever a request is made to /logs/something,
        the file named something is downloaded from the current log folder"""
        result = flask.send_from_directory(ms.log_directory, path)
        return result

    return app
