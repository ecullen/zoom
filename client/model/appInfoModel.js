define(['jquery', 'knockout' ], function($, ko){
return function AppInfoModel(configPath, login) {
    // Application info box
    var self = this;

    self.data = ko.observable("");
    self.showInfo = ko.observable(false);
    self.maxLength = 120;

    self.toggle = function () {
        self.showInfo(!self.showInfo());
    };

    self.save = function () {
        self.data(document.getElementsByName(configPath)[0].textContent);
        if (self.data().length > 120){
            alert("The maximum comment length is 120 characters. It will not be saved until it is shorter.");
            return;
        }
        var dict = {
            loginName: login.elements.username(),
            configurationPath: configPath,
            serviceInfo: self.data()
        };

        $.post("/api/serviceinfo/", dict).fail(function (data) {
            alert("Error Posting ServiceInfo " + JSON.stringify(data));
        });
    };

    self.getInfo = ko.computed(function () {
        if (self.showInfo()) {
            var dict = {configurationPath: configPath};
            if (self.showInfo()) {
                $.getJSON("/api/serviceinfo/", dict, function (data) {
                    self.data(data.servicedata);
                }).fail(function (data) {
                    alert("Failed Get for ServiceInfo " + JSON.stringify(data));
                });
            }
        }
    });

}});
