// Note: cannot use the '$' variable in here because Django turns on 
// jQuery.noConflict() for the admin interface.

jQuery(document).ready(function () {

  var wymconfig = {
    skin: 'custom',
    toolsItems: [
      {'name': 'Bold', 'title': 'Strong', 'css': 'wym_tools_strong'}, 
      {'name': 'Italic', 'title': 'Emphasis', 'css': 'wym_tools_emphasis'},
      {'name': 'InsertOrderedList', 'title': 'Ordered_List', 'css': 'wym_tools_ordered_list'},
      {'name': 'InsertUnorderedList', 'title': 'Unordered_List', 'css': 'wym_tools_unordered_list'},
      {'name': 'Undo', 'title': 'Undo', 'css': 'wym_tools_undo'},
      {'name': 'Redo', 'title': 'Redo', 'css': 'wym_tools_redo'},
      {'name': 'CreateLink', 'title': 'Link', 'css': 'wym_tools_link'},
      {'name': 'Unlink', 'title': 'Unlink', 'css': 'wym_tools_unlink'},
      {'name': 'ToggleHtml', 'title': 'HTML', 'css': 'wym_tools_html'}
    ],
    updateSelector: 'input:submit',
    updateEvent: 'click',
    classesHtml: ''
  };

  // Initialize WYMeditors.
  jQuery('textarea:not([id*=__prefix__])').wymeditor(wymconfig);
  jQuery('body').bind('addedinlinerow', function (event, row) {
    jQuery('#' + row.id).find('textarea').wymeditor(wymconfig);
  });

  // Initialize timeago.
  jQuery('time.timeago').timeago();
});