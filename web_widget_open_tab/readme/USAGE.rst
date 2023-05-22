Edit the tree view and add the widget as the first field, usually, we should use:
.. code-block:: xml

    <field name="id" widget="open_tab"/>

You can open the record in a new tab when clicking with the mouse wheel on the external link icon.
On a usual click the record will be opened without changes (keeping the breadcrumbs).

You can also add open_tab feature in tree by checking "Open Tab Field in List" field (open_tab) in ir.model.
For instance, if you check this field in sale.order model, then you will see open tab feature in sale order tree view.
