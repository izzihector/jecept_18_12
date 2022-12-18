odoo.define('client_act.BillReport', function (require) {
   'use strict';
   var AbstractAction = require('web.AbstractAction');
   var core = require('web.core');
   var rpc = require('web.rpc');
   var QWeb = core.qweb;
   var BillReport = AbstractAction.extend({
   template: 'BillReport',
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
               model: 'bill.report',
               method: 'get_report_lines',
               args: [self.filters],
           }).then(function(report_lines) {
               self.$('.table_view').html( QWeb.render('BillReportLines', {report_lines: report_lines, filters: self.filters}) );
           });
       },
   });

   core.action_registry.add("BillReport", BillReport);
   return BillReport;
});

