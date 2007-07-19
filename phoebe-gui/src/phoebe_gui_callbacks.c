#include <phoebe/phoebe.h>

#include "phoebe_gui_base.h"
#include "phoebe_gui_treeviews.h"
#include "phoebe_gui_callbacks.h"


/* ******************************************************************** *
 *
 *                    phoebe_data_lc_treeview events
 *
 * ******************************************************************** */


void
on_phoebe_data_lc_treeview_row_activated
                                        (GtkTreeView      *treeview,
                                        GtkTreePath       *path,
                                        GtkTreeViewColumn *column,
                                        gpointer           user_data)
{

}


void
on_phoebe_data_lc_treeview_cursor_changed
                                        (GtkTreeView *tree_view,
                                         gpointer     user_data)
{

}


void
on_phoebe_data_lc_add_button_clicked   (GtkButton       *button,
                                        gpointer         user_data)
{
    GladeXML  *phoebe_load_lc_xml                   = glade_xml_new       ("../glade/phoebe_load_lc.glade", NULL, NULL);

    GtkWidget *phoebe_load_lc_dialog                = glade_xml_get_widget(phoebe_load_lc_xml, "phoebe_load_lc_dialog");
	GtkWidget *phoebe_load_lc_filechooserbutton     = glade_xml_get_widget(phoebe_load_lc_xml, "phoebe_load_lc_filechooserbutton");
    GtkWidget *phoebe_load_lc_column1_combobox      = glade_xml_get_widget(phoebe_load_lc_xml, "phoebe_load_lc_column1_combobox");
    GtkWidget *phoebe_load_lc_column2_combobox      = glade_xml_get_widget(phoebe_load_lc_xml, "phoebe_load_lc_column2_combobox");
    GtkWidget *phoebe_load_lc_column3_combobox      = glade_xml_get_widget(phoebe_load_lc_xml, "phoebe_load_lc_column3_combobox");
    GtkWidget *phoebe_load_lc_sigma_spinbutton      = glade_xml_get_widget(phoebe_load_lc_xml, "phoebe_load_lc_sigma_spinbutton");
    GtkWidget *phoebe_load_lc_filter_combobox       = glade_xml_get_widget(phoebe_load_lc_xml, "phoebe_load_lc_filter_combobox");
    GtkWidget *phoebe_load_lc_reddening_checkbutton = glade_xml_get_widget(phoebe_load_lc_xml, "phoebe_load_lc_reddening_checkbutton");
    GtkWidget *pphoebe_load_lc_r_spinbutton         = glade_xml_get_widget(phoebe_load_lc_xml, "phoebe_load_lc_r_spinbutton");
    GtkWidget *phoebe_load_lc_e_spinbutton          = glade_xml_get_widget(phoebe_load_lc_xml, "phoebe_load_lc_e_spinbutton");
    GtkWidget *phoebe_load_lc_preview_textview      = glade_xml_get_widget(phoebe_load_lc_xml, "phoebe_load_lc_preview_textview");

    g_object_unref(phoebe_load_lc_xml);

    int result = gtk_dialog_run ((GtkDialog*)phoebe_load_lc_dialog);
    int combo_item;

    char *filename;
    char *itype;
    char *dtype;
    char *wtype;
    char *filter;

    switch (result)
    {
        case GTK_RESPONSE_OK:

            filename = gtk_file_chooser_get_filename ((GtkFileChooser*)phoebe_load_lc_filechooserbutton);

            combo_item = gtk_combo_box_get_active((GtkComboBox*)phoebe_load_lc_column1_combobox);
            switch (combo_item)
            {
                case 0:
                    itype = "Time";
                    break;
                case 1:
                    itype = "Phase";
                    break;
                default:
                    itype = "Time";
                    break;
            }

            combo_item = gtk_combo_box_get_active((GtkComboBox*)phoebe_load_lc_column2_combobox);
            switch (combo_item)
            {
                case 0:
                    dtype = "Flux";
                    break;
                case 1:
                    dtype = "Magnitude";
                    break;
                default:
                    dtype = "Flux";
                    break;
            }

            combo_item = gtk_combo_box_get_active((GtkComboBox*)phoebe_load_lc_column3_combobox);
            switch (combo_item)
            {
                case 0:
                    wtype = "Weight (int)";
                    break;
                case 1:
                    wtype = "Weight (real)";
                    break;
                case 2:
                    wtype = "Absolute error";
                case 3:
                    wtype = "Unavailable";
                default:
                    wtype = "Unavailable";
                    break;
            }

            filter = "Undefined"; /* TODO: get the filter */

            GtkTreeModel *model;
            model = gtk_tree_view_get_model((GtkTreeView*)phoebe_data_lc_treeview);

            GtkTreeIter iter;
            gtk_list_store_append((GtkListStore*)model, &iter);
            gtk_list_store_set((GtkListStore*)model, &iter, LC_COL_ACTIVE,      TRUE,
                                                            LC_COL_FILENAME,    filename,
                                                            LC_COL_FILTER,      filter,
                                                            LC_COL_ITYPE,       itype,
                                                            LC_COL_DTYPE,       dtype,
                                                            LC_COL_WTYPE,       wtype,
                                                            LC_COL_SIGMA,       gtk_spin_button_get_value((GtkSpinButton*)phoebe_load_lc_sigma_spinbutton),
                                                            LC_COL_LEVWEIGHT,   "Poissonian scatter",
                                                            LC_COL_HLA,         12.566371,
                                                            LC_COL_CLA,         12.566371,
                                                            LC_COL_OPSF,        0.0,
                                                            LC_COL_EL3,         0.0,
                                                            LC_COL_EXTINCTION,  0.0,
                                                            LC_COL_X1,          0.5,
                                                            LC_COL_X2,          0.5,
                                                            LC_COL_Y1,          0.5,
                                                            LC_COL_Y2,          0.5, -1);
            break;
        case GTK_RESPONSE_CANCEL:
            break;
    }
    gtk_widget_destroy (phoebe_load_lc_dialog);
}


void
on_phoebe_data_lc_edit_button_clicked  (GtkButton       *button,
                                        gpointer         user_data)
{

}


void
on_phoebe_data_lc_remove_button_clicked
                                        (GtkButton       *button,
                                        gpointer         user_data)
{
    GtkTreeSelection *selection;
    GtkTreeModel     *model;
    GtkTreeIter       iter;

    selection = gtk_tree_view_get_selection((GtkTreeView*)phoebe_data_lc_treeview);
    if (gtk_tree_selection_get_selected(selection, &model, &iter))
    {
        gtk_list_store_remove((GtkListStore*)model, &iter);
    }
}


void on_phoebe_data_lc_active_checkbutton_toggled
                                        (GtkCellRendererToggle *renderer,
                                         gchar                 *path,
                                         gpointer               user_data)
{
    GtkTreeModel *model;
    GtkTreeIter iter;
    int active;

    model = gtk_tree_view_get_model((GtkTreeView*)phoebe_data_lc_treeview);

    if(gtk_tree_model_get_iter_from_string(model, &iter, path))
    {
        g_object_get(renderer, "active", &active, NULL);

        if(active) gtk_list_store_set((GtkListStore*)model, &iter, LC_COL_ACTIVE, FALSE, -1);
        else       gtk_list_store_set((GtkListStore*)model, &iter, LC_COL_ACTIVE, TRUE, -1);
    }
}


/* ******************************************************************** *
 *
 *                    phoebe_data_rv_treeview events
 *
 * ******************************************************************** */


void
on_phoebe_data_rv_treeview_row_activated
                                        (GtkTreeView        *treeview,
                                         GtkTreePath        *path,
                                         GtkTreeViewColumn  *column,
                                         gpointer            user_data)
{

}


void
on_phoebe_data_rv_treeview_cursor_changed
                                        (GtkTreeView *tree_view,
                                         gpointer     user_data)
{

}


void
on_phoebe_data_rv_add_button_clicked   (GtkButton       *button,
                                        gpointer         user_data)
{
    GladeXML  *phoebe_load_rv_xml                   = glade_xml_new       ("../glade/phoebe_load_rv.glade", NULL, NULL);

    GtkWidget *phoebe_load_rv_dialog                = glade_xml_get_widget(phoebe_load_rv_xml, "phoebe_load_rv_dialog");
	GtkWidget *phoebe_load_rv_filechooserbutton     = glade_xml_get_widget(phoebe_load_rv_xml, "phoebe_load_rv_filechooserbutton");
    GtkWidget *phoebe_load_rv_column1_combobox      = glade_xml_get_widget(phoebe_load_rv_xml, "phoebe_load_rv_column1_combobox");
    GtkWidget *phoebe_load_rv_column2_combobox      = glade_xml_get_widget(phoebe_load_rv_xml, "phoebe_load_rv_column2_combobox");
    GtkWidget *phoebe_load_rv_column3_combobox      = glade_xml_get_widget(phoebe_load_rv_xml, "phoebe_load_rv_column3_combobox");
    GtkWidget *phoebe_load_rv_sigma_spinbutton      = glade_xml_get_widget(phoebe_load_rv_xml, "phoebe_load_rv_sigma_spinbutton");
    GtkWidget *phoebe_load_rv_filter_combobox       = glade_xml_get_widget(phoebe_load_rv_xml, "phoebe_load_rv_filter_combobox");
    GtkWidget *phoebe_load_lc_preview_textview      = glade_xml_get_widget(phoebe_load_rv_xml, "phoebe_load_rv_preview_textview");

    g_object_unref(phoebe_load_rv_xml);

    int result = gtk_dialog_run ((GtkDialog*)phoebe_load_rv_dialog);
    int combo_item;

    char *filename;
    char *itype;
    char *dtype;
    char *wtype;
    char *filter;

    switch (result)
    {
        case GTK_RESPONSE_OK:

            filename = gtk_file_chooser_get_filename ((GtkFileChooser*)phoebe_load_rv_filechooserbutton);

            combo_item = gtk_combo_box_get_active((GtkComboBox*)phoebe_load_rv_column1_combobox);
            switch (combo_item)
            {
                case 0:
                    itype = "Time";
                    break;
                case 1:
                    itype = "Phase";
                    break;
                default:
                    itype = "Time";
                    break;
            }

            combo_item = gtk_combo_box_get_active((GtkComboBox*)phoebe_load_rv_column2_combobox);
            switch (combo_item)
            {
                case 0:
                    dtype = "RV in km/h";
                    break;
                case 1:
                    dtype = "Rv in 100km/h";
                    break;
                default:
                    dtype = "RV in km/h";
                    break;
            }

            combo_item = gtk_combo_box_get_active((GtkComboBox*)phoebe_load_rv_column3_combobox);
            switch (combo_item)
            {
                case 0:
                    wtype = "Weight (int)";
                    break;
                case 1:
                    wtype = "Weight (real)";
                    break;
                case 2:
                    wtype = "Absolute error";
                case 3:
                    wtype = "Unavailable";
                default:
                    wtype = "Unavailable";
                    break;
            }

            filter = "Undefined"; /* TODO: get the filter */

            GtkTreeModel *model;
            model = gtk_tree_view_get_model((GtkTreeView*)phoebe_data_rv_treeview);

            GtkTreeIter iter;
            gtk_list_store_append((GtkListStore*)model, &iter);
            gtk_list_store_set((GtkListStore*)model, &iter, RV_COL_ACTIVE,      TRUE,
                                                            RV_COL_FILENAME,    filename,
                                                            RV_COL_FILTER,      filter,
                                                            RV_COL_ITYPE,       itype,
                                                            RV_COL_DTYPE,       dtype,
                                                            RV_COL_WTYPE,       wtype,
                                                            RV_COL_SIGMA,       gtk_spin_button_get_value((GtkSpinButton*)phoebe_load_rv_sigma_spinbutton),
                                                            RV_COL_X1,          0.5,
                                                            RV_COL_X2,          0.5,
                                                            RV_COL_Y1,          0.5,
                                                            RV_COL_Y2,          0.5, -1);
            break;
        case GTK_RESPONSE_CANCEL:
            break;
    }
    gtk_widget_destroy (phoebe_load_rv_dialog);
}


void
on_phoebe_data_rv_edit_button_clicked  (GtkButton       *button,
                                        gpointer         user_data)
{

}


void
on_phoebe_data_rv_remove_button_clicked
                                        (GtkButton       *button,
                                        gpointer         user_data)
{
    GtkTreeSelection *selection;
    GtkTreeModel     *model;
    GtkTreeIter       iter;

    selection = gtk_tree_view_get_selection((GtkTreeView*)phoebe_data_rv_treeview);
    if (gtk_tree_selection_get_selected(selection, &model, &iter))
    {
        gtk_list_store_remove((GtkListStore*)model, &iter);
    }
}


void on_phoebe_data_rv_active_checkbutton_toggled
                                        (GtkCellRendererToggle *renderer,
                                         gchar                 *path,
                                         gpointer               user_data)
{
    GtkTreeModel *model;
    GtkTreeIter iter;
    int active;

    model = gtk_tree_view_get_model((GtkTreeView*)phoebe_data_rv_treeview);

    if(gtk_tree_model_get_iter_from_string(model, &iter, path))
    {
        g_object_get(renderer, "active", &active, NULL);

        if(active) gtk_list_store_set((GtkListStore*)model, &iter, RV_COL_ACTIVE, FALSE, -1);
        else       gtk_list_store_set((GtkListStore*)model, &iter, RV_COL_ACTIVE, TRUE, -1);
    }
}


/* ******************************************************************** *
 *
 *               phoebe_para_surf_spots_treeview events
 *
 * ******************************************************************** */


void
on_phoebe_para_surf_spots_treeview_row_activated
                                        (GtkTreeView      *treeview,
                                        GtkTreePath       *path,
                                        GtkTreeViewColumn *column,
                                        gpointer           user_data)
{

}


void
on_phoebe_para_surf_spots_treeview_cursor_changed
                                        (GtkTreeView *tree_view,
                                         gpointer     user_data)
{

}

void
on_phoebe_para_surf_spots_add_button_clicked   (GtkButton       *button,
                                                gpointer         user_data)
{
    GladeXML  *phoebe_load_spots_xml                    = glade_xml_new       ("../glade/phoebe_load_spots.glade", NULL, NULL);

	GtkWidget *phoebe_load_spots_dialog                 = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_dialog");
	GtkWidget *phoebe_load_spots_lat_spinbutton         = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_lat_spinbutton");
	GtkWidget *phoebe_load_spots_latadjust_checkbutton  = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_latadjust_checkbutton");
	GtkWidget *phoebe_load_spots_latstep_spinbutton     = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_latstep_spinbutton");
	GtkWidget *phoebe_load_spots_latmax_spinbutton      = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_latmax_spinbutton");
	GtkWidget *phoebe_load_spots_latmin_spinbutton      = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_latmin_spinbutton");
	GtkWidget *phoebe_load_spots_lon_spinbutton         = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_lon_spinbutton");
	GtkWidget *phoebe_load_spots_lonadjust_checkbutton  = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_lonadjust_checkbutton");
	GtkWidget *phoebe_load_spots_lonstep_spinbutton     = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_lonstep_spinbutton");
	GtkWidget *phoebe_load_spots_lonmax_spinbutton      = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_lonmax_spinbutton");
	GtkWidget *phoebe_load_spots_lonmin_spinbutton      = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_lonmin_spinbutton");
	GtkWidget *phoebe_load_spots_rad_spinbutton         = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_rad_spinbutton");
	GtkWidget *phoebe_load_spots_radadjust_checkbutton  = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_radadjust_checkbutton");
	GtkWidget *phoebe_load_spots_radstep_spinbutton     = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_radstep_spinbutton");
	GtkWidget *phoebe_load_spots_radmax_spinbutton      = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_radmax_spinbutton");
	GtkWidget *phoebe_load_spots_radmin_spinbutton      = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_radmin_spinbutton");
	GtkWidget *phoebe_load_spots_temp_spinbutton        = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_temp_spinbutton");
	GtkWidget *phoebe_load_spots_tempadjust_checkbutton = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_tempadjust_checkbutton");
	GtkWidget *phoebe_load_spots_tempstep_spinbutton    = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_tempstep_spinbutton");
	GtkWidget *phoebe_load_spots_tempmax_spinbutton     = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_tempmax_spinbutton");
	GtkWidget *phoebe_load_spots_tempmin_spinbutton     = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_tempmin_spinbutton");
	GtkWidget *phoebe_load_spots_source_combobox        = glade_xml_get_widget(phoebe_load_spots_xml, "phoebe_load_spots_source_combobox");

	g_object_unref(phoebe_load_spots_xml);

	int result = gtk_dialog_run ((GtkDialog*)phoebe_load_spots_dialog);
	int combo_item;
	char *source;

	switch (result)
	{
	    case GTK_RESPONSE_OK:

            combo_item = gtk_combo_box_get_active ((GtkComboBox*)phoebe_load_spots_source_combobox);
            switch (combo_item)
            {
                case 0:
                    source = "Primary star";
                    break;
                case 1:
                    source = "Secondary star";
                    break;
                default:
                    source = "Primary star";
                    break;
            }

            GtkTreeModel *model;
            model = gtk_tree_view_get_model((GtkTreeView*)phoebe_para_surf_spots_treeview);

            GtkTreeIter iter;
            gtk_list_store_append((GtkListStore*)model, &iter);
            gtk_list_store_set((GtkListStore*)model, &iter, SPOTS_COL_ADJUST,       FALSE,
                                                            SPOTS_COL_SOURCE,       source,
                                                            SPOTS_COL_LAT,          gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_lat_spinbutton),
                                                            SPOTS_COL_LATADJUST,    gtk_toggle_button_get_active((GtkToggleButton*)phoebe_load_spots_latadjust_checkbutton),
                                                            SPOTS_COL_LATSTEP,      gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_latstep_spinbutton),
                                                            SPOTS_COL_LATMIN,       gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_latmin_spinbutton),
                                                            SPOTS_COL_LATMAX,       gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_latmax_spinbutton),
                                                            SPOTS_COL_LON,          gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_lon_spinbutton),
                                                            SPOTS_COL_LONADJUST,    gtk_toggle_button_get_active((GtkToggleButton*)phoebe_load_spots_lonadjust_checkbutton),
                                                            SPOTS_COL_LONSTEP,      gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_lonstep_spinbutton),
                                                            SPOTS_COL_LONMIN,       gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_lonmin_spinbutton),
                                                            SPOTS_COL_LONMAX,       gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_lonmax_spinbutton),
                                                            SPOTS_COL_RAD,          gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_rad_spinbutton),
                                                            SPOTS_COL_RADADJUST,    gtk_toggle_button_get_active((GtkToggleButton*)phoebe_load_spots_radadjust_checkbutton),
                                                            SPOTS_COL_RADSTEP,      gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_radstep_spinbutton),
                                                            SPOTS_COL_RADMIN,       gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_radmin_spinbutton),
                                                            SPOTS_COL_RADMAX,       gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_radmax_spinbutton),
                                                            SPOTS_COL_TEMP,         gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_temp_spinbutton),
                                                            SPOTS_COL_TEMPADJUST,   gtk_toggle_button_get_active((GtkToggleButton*)phoebe_load_spots_tempadjust_checkbutton),
                                                            SPOTS_COL_TEMPSTEP,     gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_tempstep_spinbutton),
                                                            SPOTS_COL_TEMPMIN,      gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_tempmin_spinbutton),
                                                            SPOTS_COL_TEMPMAX,      gtk_spin_button_get_value   ((GtkSpinButton*)  phoebe_load_spots_tempmax_spinbutton), -1);
            break;
        case GTK_RESPONSE_CANCEL:
            break;
	}

    gtk_widget_destroy (phoebe_load_spots_dialog);
}


void
on_phoebe_para_surf_spots_edit_button_clicked  (GtkButton       *button,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_spots_remove_button_clicked
                                        (GtkButton       *button,
                                        gpointer         user_data)
{
    GtkTreeSelection *selection;
    GtkTreeModel     *model;
    GtkTreeIter       iter;

    selection = gtk_tree_view_get_selection((GtkTreeView*)phoebe_para_surf_spots_treeview);
    if (gtk_tree_selection_get_selected(selection, &model, &iter))
    {
        gtk_list_store_remove((GtkListStore*)model, &iter);
    }
}


void on_phoebe_para_surf_spots_adjust_checkbutton_toggled
                                        (GtkCellRendererToggle *renderer,
                                         gchar                 *path,
                                         gpointer               user_data)
{
    GtkTreeModel *model;
    GtkTreeIter iter;
    int active;

    model = gtk_tree_view_get_model((GtkTreeView*)phoebe_para_surf_spots_treeview);

    if(gtk_tree_model_get_iter_from_string(model, &iter, path))
    {
        g_object_get(renderer, "active", &active, NULL);

        if(active) gtk_list_store_set((GtkListStore*)model, &iter, SPOTS_COL_ADJUST, FALSE, -1);
        else       gtk_list_store_set((GtkListStore*)model, &iter, SPOTS_COL_ADJUST, TRUE, -1);
    }
}


/* ******************************************************************** *
 *
 *                    phoebe_window menubar events
 *
 * ******************************************************************** */


gboolean
on_phoebe_window_delete_event          (GtkWidget *widget,
                                        GdkEvent  *event,
                                        gpointer   user_data)
{
    gtk_main_quit();
}


void
on_phoebe_file_new_menuitem_activate   (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{

}


void
on_phoebe_file_open_menuitem_activate  (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{

}


void
on_phoebe_file_save_menuitem_activate  (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{

}


void
on_phoebe_file_saveas_menuitem_activate
                                       (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{

}


void
on_phoebe_file_quit_menuitem_activate  (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{
    gtk_main_quit();
}


void
on_phoebe_settings_configuration_menuitem_activate
                                       (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{

}


void
on_phoebe_help_about_menuitem_activate (GtkMenuItem     *menuitem,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_window toolbar events
 *
 * ******************************************************************** */


void
on_phoebe_lc_plot_toolbutton_clicked  (GtkToolButton   *toolbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_rv_plot_toolbutton_clicked  (GtkToolButton   *toolbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_fiitting_toolbutton_clicked  (GtkToolButton   *toolbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_scripter_toolbutton_clicked  (GtkToolButton   *toolbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_settings_toolbutton_clicked  (GtkToolButton   *toolbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_quit_toolbutton_clicked      (GtkToolButton   *toolbutton,
                                        gpointer         user_data)
{
    gtk_main_quit();
}


void
on_phoebe_open_toolbutton_clicked      (GtkToolButton   *toolbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_save_toolbutton_clicked      (GtkToolButton   *toolbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_window data tab events
 *
 * ******************************************************************** */


void
on_phoebe_data_star_name_entry_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_data_star_model_combobox_changed
                                        (GtkComboBox     *combobox,
                                        gpointer         user_data)
{

}


void
on_phoebe_data_lcoptions_mag_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_data_lcoptions_mag_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_data_rvoptions_psepe_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_data_rvoptions_ssepe_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_data_options_bins_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_data_options_binsno_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_data_options_binsno_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_data_options_the_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_data_options_the_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_eph_dpdt events
 *
 * ******************************************************************** */


void
on_phoebe_para_eph_dpdt_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dpdt_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dpdtadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dpdtstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dpdtstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dpdtmax_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dpdtmax_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dpdtmin_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dpdtmin_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_eph_period events
 *
 * ******************************************************************** */


void
on_phoebe_para_eph_periodmin_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_periodmin_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_periodmax_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_periodmax_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_periodstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_periodstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_periodadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_period_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_period_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_eph_hjd0 events
 *
 * ******************************************************************** */


void
on_phoebe_para_eph_hjd0_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_hjd0_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_hjd0adjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_hjd0step_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_hjd0step_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_hjd0max_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_hjd0max_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_hjd0min_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_hjd0min_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_eph_dperdt events
 *
 * ******************************************************************** */


void
on_phoebe_para_eph_dperdt_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dperdt_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dperdtadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dperdtstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dperdtstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dperdtmax_spinbutton_remove_widget
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dperdtmax_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dperdtmin_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_dperdtmin_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_eph_perr0 events
 *
 * ******************************************************************** */


void
on_phoebe_para_eph_perr0min_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_perr0min_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_perr0max_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_perr0max_spinbutton_change_value
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_perr0step_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_perr0step_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_perr0adjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_perr0_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_perr0_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_eph_pshift events
 *
 * ******************************************************************** */


void
on_phoebe_para_eph_pshiftmin_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_pshiftmin_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_pshiftmax_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_pshiftmax_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_pshiftstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_pshiftstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_eph_pshiftadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_sys_incl events
 *
 * ******************************************************************** */


void
on_phoebe_para_sys_incl_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_incl_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_incladjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_inclstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_inclstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_inclmax_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_inclmax_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_inclmin_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_inclmin_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_sys_ecc events
 *
 * ******************************************************************** */


void
on_phoebe_para_sys_ecc_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_ecc_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_eccadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_eccstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_eccstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_eccmax_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_eccmax_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_eccmin_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_eccmin_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_sys_vga events
 *
 * ******************************************************************** */


void
on_phoebe_para_sys_vgamin_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_vgamin_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_vgamax_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_vgamax_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_vgastep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_vgastep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_vgaadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_vga_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_vga_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_sys_rm events
 *
 * ******************************************************************** */


void
on_phoebe_para_sys_rm_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_rm_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_rmadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_rmstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_rmstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_rmmax_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_rmmax_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_rmmin_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_rmmin_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_sys_sma events
 *
 * ******************************************************************** */


void
on_phoebe_para_sys_smamin_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_smamin_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_smamax_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_smamax_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_smastep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_smastep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_smaadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_sma_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_sma_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_sys_f1 events
 *
 * ******************************************************************** */


void
on_phoebe_para_sys_f1min_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f1min_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f1max_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f1max_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f1step_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f1step_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f1adjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f1_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f1_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_sys_f2 events
 *
 * ******************************************************************** */


void
on_phoebe_para_sys_f2_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f2_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f2adjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f2step_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f2step_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f2max_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f2max_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f2min_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_sys_f2min_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_comp_met2 events
 *
 * ******************************************************************** */


void
on_phoebe_para_comp_met2min_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met2min_spinbutton_wrapped
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met2max_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met2max_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met2step_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met2step_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met2adjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met2_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met2_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_comp_met1 events
 *
 * ******************************************************************** */


void
on_phoebe_para_comp_met1_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met1_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met1adjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met1step_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met1step_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met1max_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met1max_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met1min_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_met1min_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_comp_pcsv events
 *
 * ******************************************************************** */


void
on_phoebe_para_comp_pcsv_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_pcsv_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_pcsvadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_pcsvstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_pcsvstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_pcsvmax_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_pcsvmax_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_pcsvmin_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_pcsvmin_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_comp_phsv events
 *
 * ******************************************************************** */


void
on_phoebe_para_comp_phsvmin_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_phsvmin_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_phsvmax_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_phsvmax_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_phsvstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_phsvstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_phsvadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_phsv_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_phsv_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_comp_tavc events
 *
 * ******************************************************************** */


void
on_phoebe_para_comp_tavc_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavc_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavcadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavcstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavcstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavcmax_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavcmax_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavcmin_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavcmin_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_comp_tavh events
 *
 * ******************************************************************** */


void
on_phoebe_para_comp_tavhmin_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavhmin_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavhmax_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavhmax_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavhstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavhstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavh_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavh_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_tavh_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_comp_logg1 events
 *
 * ******************************************************************** */


void
on_phoebe_para_comp_logg1min_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg1min_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg1max_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg1max_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg1step_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg1step_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg1adjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg1_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg1_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_comp_logg2 events
 *
 * ******************************************************************** */


void
on_phoebe_para_comp_logg2_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg2_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg2adjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg2step_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg2step_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg2max_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg2max_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg2min_spinbutton_remove_widget
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_comp_logg2min_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_surf_alb1 events
 *
 * ******************************************************************** */


void
on_phoebe_para_surf_alb1_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb1_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb1adjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb1step_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb1step_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb1max_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb1max_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb1min_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb1min_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_surf_alb2 events
 *
 * ******************************************************************** */


void
on_phoebe_para_surf_alb2min_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb2min_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb2max_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb2max_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb2step_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb2step_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb2adjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb2_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_alb2_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_surf_gr1 events
 *
 * ******************************************************************** */


void
on_phoebe_para_surf_gr1_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr1_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr1adjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr1step_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr1step_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr1max_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr1max_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr1min_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr1min_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_surf_gr2 events
 *
 * ******************************************************************** */


void
on_phoebe_para_surf_gr2min_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr2min_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr2max_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr2max_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr2step_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr2step_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr2adjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr2_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_surf_gr2_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_lum_levels events
 *
 * ******************************************************************** */


void
on_phoebe_para_lum_levels_treeview_row_activated
                                        (GtkTreeView     *treeview,
                                        GtkTreePath     *path,
                                        GtkTreeViewColumn *column,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_levels_edit_button_clicked
                                        (GtkButton       *button,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_levels_primadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_levels_secadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_levels_primstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_levels_primstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_levels_secstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_levels_secstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_lum_el3 events
 *
 * ******************************************************************** */


void
on_phoebe_para_lum_el3_treeview_row_activated
                                        (GtkTreeView     *treeview,
                                        GtkTreePath     *path,
                                        GtkTreeViewColumn *column,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_el3_opacityadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_el3_opacitystep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_el3_opacitystep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_el3ajdust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_el3step_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_el3step_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_lum_weighting events
 *
 * ******************************************************************** */


void
on_phoebe_para_lum_weighting_treeview_row_activated
                                        (GtkTreeView     *treeview,
                                        GtkTreePath     *path,
                                        GtkTreeViewColumn *column,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_weighting_edit_button_clicked
                                        (GtkButton       *button,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_lum_atmospheres events
 *
 * ******************************************************************** */


void
on_phoebe_para_lum_atmospheres_prim_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_atmospheres_sec_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_atmospheres_grav_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_lum_noise events
 *
 * ******************************************************************** */


void
on_phoebe_para_lum_noise_seed_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_noise_seed_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_noise_seedgen_button_clicked
                                        (GtkButton       *button,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_noise_sigma_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_noise_sigma_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_noise_lcscatter_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_noise_lcscatter_combobox_changed
                                        (GtkComboBox     *combobox,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_options_reflections_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_lum_options events
 *
 * ******************************************************************** */


void
on_phoebe_para_lum_options_decouple_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_options_reflections_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_lum_options_reflections_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_ld_bolcoefs events
 *
 * ******************************************************************** */


void
on_phoebe_para_ld_bolcoefs_secy_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_bolcoefs_secy_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_bolcoefs_primy_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_bolcoefs_primy_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_bolcoefs_secx_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_bolcoefs_secx_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_bolcoefs_primx_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_bolcoefs_primx_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_model_autoupdate_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_ld_model events
 *
 * ******************************************************************** */


void
on_phoebe_para_ld_model_combobox_changed
                                        (GtkComboBox     *combobox,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_model_tables_claret_button_clicked
                                        (GtkButton       *button,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_model_tables_vanhamme_button_clicked
                                        (GtkButton       *button,
                                        gpointer         user_data)
{

}


/* ******************************************************************** *
 *
 *                    phoebe_para_ld_lccoefs events
 *
 * ******************************************************************** */


void
on_phoebe_para_ld_lccoefs_treeview_row_activated
                                        (GtkTreeView     *treeview,
                                        GtkTreePath     *path,
                                        GtkTreeViewColumn *column,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_lccoefs_secstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_lccoefs_secstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_lccoefs_primstep_spinbutton_editing_done
                                        (GtkCellEditable *celleditable,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_lccoefs_primstep_spinbutton_value_changed
                                        (GtkSpinButton   *spinbutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_lccoefs_secadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}


void
on_phoebe_para_ld_lccoefs_primadjust_checkbutton_toggled
                                        (GtkToggleButton *togglebutton,
                                        gpointer         user_data)
{

}
