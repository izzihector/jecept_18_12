odoo.define('client_act.InvoiceReport', function (require) {
   'use strict';
   var AbstractAction = require('web.AbstractAction');
   var core = require('web.core');
   var rpc = require('web.rpc');
   var QWeb = core.qweb;
   var InvoiceReport = AbstractAction.extend({
   template: 'InvoiceReport',
       events: {
       },
       init: function(parent, action) {
           this._super(parent, action);
           this.filters = action.filters || {};
//           console.log('action', this.action)
       },

       start: function() {
           var self = this;
           self.load_data();
       },

       load_data: function () {
           var self = this;
//           console.log('filters', this.filters)
           self._rpc({
               model: 'invoice.report',
               method: 'get_report_lines',
               args: [self.filters],
           }).then(function(report_lines) {
               self.$('.table_view').html( QWeb.render('InvoiceReportLines', {report_lines: report_lines, filters: self.filters}) );
           });
       },
   });

   core.action_registry.add("InvoiceReport", InvoiceReport);
   return InvoiceReport;
});

