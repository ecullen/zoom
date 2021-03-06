define(
    [
        'jquery',
        'knockout',
        'classes/applicationStateArray',
        'model/graphiteModel',
        'model/appInfoModel',
        'model/dependencyModel',
        'model/toolsModel',
        'model/constants'
    ],
    function($, ko, ApplicationStateArray, GraphiteModel, AppInfoModel, DependencyModel, ToolsModel, constants) {
        return function ApplicationState(data, parent) {
            var self = this;

            self.componentId = data.application_name;
            self.configurationPath = data.configuration_path;
            self.applicationStatus = ko.observable(data.application_status);
            self.applicationHost = ko.observable(data.application_host);
            self.applicationHostShort = ko.computed(function() {
                return self.applicationHost().split('.')[0].toUpperCase();
            });
            self.startStopTime = ko.observable(data.start_stop_time);
            self.lastUpdate = ko.observable(data.last_update);
            self.errorState = ko.observable(data.error_state);
            self.mode = ko.observable(data.local_mode);
            self.mtime = Date.now();
            self.platform = ko.observable(data.platform);
            self.graphite = new GraphiteModel(parent.environment.env().toLowerCase(), self.applicationHostShort(), self.configurationPath, self.platform());
            self.appInfo = new AppInfoModel(self.configurationPath, parent.login);
            self.dependencyModel = new DependencyModel(parent.applicationStateArray, self);
            self.toolsModel =  new ToolsModel(parent.login);
            self.loginUser = ko.observable(data.login_user);
            self.readOnly = ko.observable(data.read_only);
            self.lastCommand = ko.observable(data.last_command);
            self.grayed = ko.observable(data.grayed);
            self.pdDisabled = ko.observable(data.pd_disabled);
            self.restartCount = ko.observable(data.restart_count);
            self.progress = ko.observable(0);
            self.countdownid = ko.observable(null);
            self.loadTimes = data.load_times;
            
            self._resetProgress = ko.computed(function() {
                // if we're not starting, stop the interval function and reset progress to 0
                if (self.restartCount() == 0 || self.errorState() != constants.errorStates.starting) {
                    if (self.countdownid() !== null) {
                        clearInterval(self.countdownid());
                        self.countdownid(null)
                    }
                    self.progress(0);
                }
            });

            self.applicationStatusClass = ko.computed(function() {
                if (self.applicationStatus().toLowerCase() === constants.applicationStatuses.running) {
                    return constants.glyphs.runningCheck;
                }
                else if (self.applicationStatus().toLowerCase() === constants.applicationStatuses.stopped) {
                    return constants.glyphs.stoppedX;
                }
                else {
                    return constants.glyphs.unknownQMark;
                }
            }, self);

            self.allChildrenUp = ko.computed(function() {
                 var down = ko.utils.arrayFirst(self.dependencyModel.upstream(), function(d) {
                     return (d.state.applicationStatus().toLowerCase() == constants.applicationStatuses.stopped)
                });

                return !down
            });

            self.applicationStatusBg = ko.computed(function() {
                if (self.grayed()) { return constants.colors.disabledGray; }
                else if (self.errorState().toLowerCase() == constants.errorStates.unknown) {
                    return constants.colors.unknownGray;
                }
                else if (self.applicationStatus().toLowerCase() === constants.applicationStatuses.running) {
                    return constants.colors.successTrans;
                }
                else if (self.applicationStatus().toLowerCase() === constants.applicationStatuses.stopped) {
                    if (self.dependencyModel.timeComponent()) {
                        return constants.colors.timeComponentPurple
                    }
                    else if (self.allChildrenUp()) {
                        return constants.colors.allDepsUpYellow
                    }
                    else {
                        return constants.colors.errorRed;
                    }
                }
                else {
                    return constants.colors.unknownGray;
                }
            }, self);

            self.modeClass = ko.computed(function() {
                if (self.mode() === parent.globalMode.current()) {
                    return '';
                }
                else if (self.mode() === 'auto') {
                    return constants.glyphs.modeAuto;
                }
                else if (self.mode() === 'manual') {
                    return constants.glyphs.modeManual;
                }
                else if (self.mode() == 'unknown') {
                    return '';
                }
                else {
                    return constants.glyphs.runningCheck;
                }

            });

            self.errorStateClass = ko.computed(function() {
                if (self.grayed()) { return constants.glyphs.grayed; }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.ok) {
                    return constants.glyphs.thumpsUp;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.started) {
                    return constants.glyphs.thumpsUp;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.stopped) {
                    return constants.glyphs.thumpsUp;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.starting) {
                    return constants.glyphs.startingRetweet;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.stopping) {
                    return constants.glyphs.stoppingDown;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.error) {
                    return constants.glyphs.errorWarning;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.notify) {
                    return constants.glyphs.notifyExclamation;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.configErr) {
                    return constants.glyphs.configErr;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.staggered) {
                    return constants.glyphs.staggeredClock;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.invalid) {
                    return constants.glyphs.invalidTrash;
                }
                else {
                    return constants.glyphs.unknownQMark;
                }
            }, self);

            self.pdDisabledClass = ko.computed(function() {
                if (self.pdDisabled()) { return constants.glyphs.pdWrench; }
                else { return ""; }
            });

            self.readOnlyClass = ko.computed(function() {
                if (self.readOnly()) { return constants.glyphs.readOnly; }
                else { return ""; }
            });

            self.errorStateBg = ko.computed(function() {
                if (self.grayed()) { return constants.colors.disabledGray; }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.ok) {
                    if (self.mode() !== parent.globalMode.current()) {
                        return constants.colors.warnOrange;
                    }
                    return constants.colors.successTrans;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.started) {
                    if (self.mode() !== parent.globalMode.current()) {
                        return constants.colors.warnOrange;
                    }
                    return constants.colors.successTrans;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.stopped) {
                    if (self.mode() !== parent.globalMode.current()) {
                        return constants.colors.warnOrange;
                    }
                    return constants.colors.successTrans;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.starting) {
                    return constants.colors.actionBlue;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.stopping) {
                    return constants.colors.actionBlue;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.error) {
                    return constants.colors.errorRed;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.notify) {
                    return constants.colors.warnOrange;
                }
                else if (self.errorState() && self.errorState().toLowerCase() === constants.errorStates.configErr) {
                    return constants.colors.configErrPink;
                }
                else {
                    return constants.colors.unknownGray;
                }
            }, self);

            self.startStopTimeTitle = ko.computed(function() {
                return 'Last: ' + self.lastCommand() + '<br>Who: ' + self.loginUser();
            });

            var getDescription = function(prop) {
                if (constants.descriptions.hasOwnProperty(prop)) {
                    return constants.descriptions[prop]
                }
                else {
                    return prop
                }
            };

            self.errorStateTitle = ko.computed(function() {
                if (self.grayed()) {return getDescription('grayed')}
                else {return getDescription(self.errorState())}
            });
            self.modeTitle = ko.computed(function() {
                return getDescription(self.mode())
            });
            self.statusTitle = ko.computed(function() {
                return getDescription(self.applicationStatus())
            });
            self.readOnlyTitle = ko.computed(function() {
                return getDescription('readOnly')
            });
            self.PDTitle = ko.computed(function() {
                return getDescription('pdDisabled')
            });

            // Creates group for sending commands
            self.groupControlStar = ko.computed(function() {
                if (parent.groupControl.indexOf(self) === -1) {
                    return constants.glyphs.emptyStar;
                }
                else {
                    return constants.glyphs.filledStar;
                }
            });

            self.groupControlStar.extend({rateLimit: 10});

            self.toggleGroupControl = function() {
                if (parent.groupControl.indexOf(self) === -1) {
                    parent.groupControl.push(self);
                }
                else {
                    parent.groupControl.remove(self);
                }
            };

            self.toggleGrayed = function() {
                var dict = {
                    'key': 'grayed',
                    'value': !self.grayed()
                };
                $.post('/api/v1/application/states' + self.configurationPath, JSON.stringify(dict))
                    .fail(function(data) { swal('Failure Toggling grayed ', JSON.stringify(data)); });
            };

            self.togglePDDisabled = function() {
                var dict = {
                    'key': 'pd_disabled',
                    'value': !self.pdDisabled()
                };
                $.post('/api/v1/application/states' + self.configurationPath, JSON.stringify(dict))
                    .fail(function(data) { swal('Failure Toggling pdDisabled ', JSON.stringify(data)); });
            };

            self.toggleDisabled = function() {
                var dict = {
                    'host': self.applicationHost(),
                    'disable': !self.readOnly(),
                    'id': self.componentId,
                    'user': parent.login.elements.username()
                };
                var t, c;
                if (self.readOnly()) {
                    c = 'Yes, enable it!';
                    t = 'This will enable startup for ' + self.componentId +'.'
                } else {
                    c = 'Yes, disable it!';
                    t = 'This will disable startup for ' + self.componentId +'. It will now be read-only.\n';
                    if (self.dependencyModel.downstream().length > 0) {
                        t += self.dependencyModel.downstream().length + ' application(s) depend on this.\n';
                        t += 'This will PREVENT these applications from starting up!'
                    }
                }
                swal({
                    title: 'Are you sure?',
                    text: t,
                    type: 'warning',
                    showCancelButton: true,
                    confirmButtonText: c,
                    cancelButtonText: 'It\'s a trap, abort!',
                    closeOnConfirm: false,
                    closeOnCancel: false
                }, function(isConfirm) {
                    if (isConfirm) {
                        $.post('/api/v1/disable', dict)
                            .success(function(data) {swal('Success!', 'Read-Only was toggled. Give it a few seconds for the change to propagate.')})
                            .fail(function(data) { swal('Failure En/Disabling app ', JSON.stringify(data)); });
                        }
                    else {
                        swal('Cancelled', 'Nothing was changed.');
                    }
                });
            };

            self.changeAppPath = function(){
                swal({   title: "Change Application Path",   
                         text:  "Current Path: "+self.configurationPath,   
                         type: "input",  
                         inputValue: "/spot/software/state/application/<add new paths>", 
                         showCancelButton: true,   
                         closeOnConfirm: false,   
                         inputPlaceholder: "New Path Here" },
                         function(inputValue) {  
                             if (inputValue === false) return false;      
                             if ((inputValue === "") || (inputValue === self.configurationPath)) {     
                                swal.showInputError("You need to write a New Path or Cancel");     
                                return false;   
                             }
                             self.toolsModel.setOldPath(self.configurationPath);
                             self.toolsModel.setNewPath(inputValue);
                             self.toolsModel.showPaths();
                          });
            };

            self.onControlAgentError = function() {
                swal('Error controlling agent.');
            };

            var countdown = function() {
                // decrement the progress integer. progress starts as the average start time of the app
                newsec = self.progress();
                newsec--;
                self.progress(newsec)
            };

            self.startCountdown = function(){
                var avgStartTime = parseInt(self.loadTimes.ave);
                if (avgStartTime === 0) {
                    self.progress('Not enough data');
                    return
                }
                // bake in 5s to run the methods on sentinel/get update from Zoom
                var adjustment = 5;
                if (self.lastUpdate() !== "") {
                    var last = Date.parse(self.lastUpdate());
                    var now = new Date();
                    timeFromUpdate = parseInt(((now.getTime() - last))/ 1000)
                }
                // if you load the page n seconds after a start, decrement n seconds from the progress number
                var sec = avgStartTime - timeFromUpdate + adjustment;
                
                self.progress(sec);
                var cdID = setInterval(countdown, 1000);
                // keep track of this id so we can stop the countdown later
                self.countdownid(cdID)
            };

            self._startCountdownAtRestart = ko.computed(function() {
                // only show when admin is enabled
                if (!parent.admin.showProgress()) {return}

                if (self.restartCount() > 0 && self.errorState() == constants.errorStates.starting) {
                    // if we already have an existing countdown, we need to stop it and start over
                    if (self.countdownid() !== null) {
                        clearInterval(self.countdownid());
                        self.countdownid(null)
                    }
                    self.startCountdown();
                }
            });

            var deleteFromZK = function() {
                // delete path from Zookeeper
                var dict = {
                    'loginName': parent.login.elements.username(),
                    'recurse': 'true',
                    'delete': self.configurationPath
                };

                $.ajax({
                    url: '/api/v1/delete/',
                    async: false,
                    data: dict,
                    type: 'POST',
                    error: function(data) {
                        swal('Error deleting path.', JSON.stringify(data.responseText), 'error');
                    }
                });
            };

            var deleteFromConfig = function() {
                // try to remove component from sentinel config
                $.get('/api/v1/config/' + self.applicationHost(), function(data) {
                    if (data !== 'Node does not exist.') {
                        var parser = new DOMParser();
                        var xmlDoc = parser.parseFromString(data, 'text/xml');
                        var found = 0;
                        var x = xmlDoc.getElementsByTagName('Component');
                        for (var i = 0; i < x.length; i++) {
                            var id = x[i].getAttribute('id');
                            if (self.configurationPath.indexOf(id, self.configurationPath.length - id.length) !== -1) {
                                x[i].parentNode.removeChild(x[i]);
                                found = found + 1;
                                i = i - 1;
                            }
                        }

                        if (found === 0) {
                            swal('Missing component', 'Didn\'t find component ' + self.configurationPath + ' in ' +
                                self.applicationHost() + '\'s config. Simply deleted the row.');
                        }
                        else if (found === 1) {
                            var oSerializer = new XMLSerializer();
                            var sXML = oSerializer.serializeToString(xmlDoc);
                            var params = {
                                'XML': sXML,
                                'serverName': self.applicationHost()
                            };
                            $.ajax(
                                {
                                    url: '/api/v1/config/' + self.applicationHost(),
                                    async: false,
                                    type: 'PUT',
                                    data: JSON.stringify(params),
                                    error: function(data) {
                                        swal('Failed putting Config', JSON.stringify(data), 'error');
                                    }
                                });
                        }
                        else {
                            swal('Multiple matches', 'Multiple components matched ' + self.configurationPath +
                                ' in ' + self.applicationHost() + '\'s config. Not deleting.');
                        }
                    }
                    else {
                        // host config did not exist. No Component to remove
                        swal('No data', 'No data for host ' + self.applicationHost());
                    }
                }).fail(function(data) {
                    swal('Failed Get Config', JSON.stringify(data));
                });
            };


            self.deleteRow = function() {
                // delete an application row on the web page
                // parses the config and deletes the component with a matching id
                // deletes the path in zookeeper matching the configurationPath
                if (self.dependencyModel.downstream().length > 0) {
                    var message = 'Are you sure?\n';
                    message += self.dependencyModel.downstream().length + ' application(s) depend on this.';
                    swal({
                        title: 'Someone depends on this!',
                        text: message,
                        type: 'warning',
                        showCancelButton: true,
                        confirmButtonText: 'Yes, delete it!',
                        cancelButtonText: 'It\'s a trap, abort!',
                        closeOnConfirm: false,
                        closeOnCancel: false
                    }, function(isConfirm) {
                        if (isConfirm) {
                            deleteFromConfig();
                            // give the agent time to clean up the old config
                            setTimeout(function() { deleteFromZK(); }, 2000);
                            swal('Deleting', 'Give us a few seconds to clean up.');
                        }
                        else {
                            swal('Cancelled', 'Nothing was deleted.');
                        }
                    });
                }
                else if (self.applicationHost() === '') {
                    swal({
                        title: 'Are you sure?',
                        text: self.configurationPath + ' has no Host listed, this delete is mostly aesthetic. Continue?',
                        type: 'warning',
                        showCancelButton: true,
                        confirmButtonText: 'Yes, delete it!',
                        cancelButtonText: 'It\'s a trap, abort!',
                        closeOnConfirm: false,
                        closeOnCancel: false
                    }, function(isConfirm) {
                        if (isConfirm) {
                            ApplicationStateArray.remove(self);
                        }
                        else {
                            swal('Cancelled', 'Nothing was deleted.');
                        }
                    });
                }
                else {
                    swal({
                        title: 'Are you sure?',
                        text: self.configurationPath + ' will be deleted, and its dependency configuration lost. Continue?',
                        type: 'warning',
                        showCancelButton: true,
                        confirmButtonText: 'Yes, delete it!',
                        cancelButtonText: 'It\'s a trap, abort!',
                        closeOnConfirm: false,
                        closeOnCancel: false
                    }, function(isConfirm) {
                        if (isConfirm) {
                            deleteFromConfig();
                            // give the agent time to clean up the old config
                            setTimeout(function() { deleteFromZK(); }, 2000);
                            swal('Deleting', 'Give us a few seconds to clean up.');
                        }
                        else {
                            swal('Cancelled', 'Nothing was deleted.');
                        }
                    });
                }
            };
        };
    });

