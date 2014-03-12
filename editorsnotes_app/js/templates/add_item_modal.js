var _ = require('underscore');

module.exports = _.template(''
  + '<div class="modal-header">'
    + '<button type="button" class="close" data-dismiss="modal">&times;</button>'
    + '<h3>Add <%= type %></h3>'
  + '</div>'
  + '<div class="modal-body">'
    + '<% if (textarea) { %>'
    + '<textarea class="item-text-main" style="width: 98%; height: 40px;"></textarea>'
    + '<% } else { %>'
    + '<input type="text" class="item-text-main" style="width: 98%;" />'
    + '<% } %>'
  + '</div>'
  + '<div class="modal-footer">'
    + '<img src="/static/style/icons/ajax-loader.gif" class="hide loader-icon pull-left">'
    + '<a href="#" class="btn" data-dismiss="modal">Cancel</a>'
    + '<a href="#" class="btn btn-primary btn-save-item">Save</a>'
  + '</div>')
