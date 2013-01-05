Ext.define('devilry_qualifiesforexam.controller.QualifiesForExamFrontpageController', {
    extend: 'Ext.app.Controller',

    views: [
        'QualifiesForExamFrontpage'
    ],

    stores: [
        'Plugins'
    ],

    requires: [
        'devilry_extjsextras.DjangoRestframeworkProxyErrorHandler',
        'devilry_extjsextras.HtmlErrorDialog'
    ],


//    refs: [{
//        ref: 'allWhereIsAdminList',
//        selector: 'allactivewhereisadminlist'
//    }],

    init: function() {
        this.control({
            'viewport frontpage': {
                render: this._onRender
            }
        });
        this.mon(this.getPluginsStore().proxy, {
            scope: this,
            exception: this._onProxyError
        });
    },

    _onRender: function() {
        this.getPluginsStore().load({
            scope: this,
            callback: function(records, op) {
                if(op.success) {
                    this._onLoadSuccess(records);
                }
                // NOTE: Errors are handled in _onProxyError
            }
        });
    },


    _onLoadSuccess: function(records) {
        console.log('success', records);

    },

    _onProxyError: function(proxy, response, operation) {
        var errorhandler = Ext.create('devilry_extjsextras.DjangoRestframeworkProxyErrorHandler');
        errorhandler.addErrors(response, operation);
        this.application.getAlertmessagelist().addMany(errorhandler.errormessages, 'error', true);
    }
});

