#include <phoebe/phoebe.h>

#include "phoebe_gui_types.h"
#include "phoebe_gui_base.h"

#include "phoebe_gui_treeviews.h"

int phoebe_gui_init ()
{
	GladeXML *phoebe_window_xml = glade_xml_new("../glade/phoebe.glade", NULL, NULL);
	phoebe_window = glade_xml_get_widget(phoebe_window_xml, "phoebe_window");
	glade_xml_signal_autoconnect(phoebe_window_xml);
    gtk_widget_show(phoebe_window);

    gui_init_treeviews(phoebe_window_xml);
	gui_init_widgets (phoebe_window_xml);

	g_object_unref(phoebe_window_xml);

	return SUCCESS;
}

int phoebe_gui_quit ()
{
	gui_free_widgets ();

	return SUCCESS;
}
