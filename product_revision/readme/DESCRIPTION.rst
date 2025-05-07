This module provides functionality to assign and manage revision data for products in Odoo 16. It allows tracking changes to products over time through a revision system.

Each revision record stores the following details:


* Name: The designation for the revision.
* Revision Number: The version or iterative identifier (automatically incremented if not provided).
* Change Date: The date when the revision was made.
* Product Internal ID: The unique internal identifier of the product.
* Notes: Additional information about the revision.
* Active status: Indicates if this is the current active revision.

Key features:


* Revisions can be linked to either product templates or product variants, but not both simultaneously.
* Only one revision can be active at a time for a given product.
* All revision history is preserved in the system for traceability.
* Integrated with Odoo's chatter system for tracking changes and activities.
* Automatic revision numbering when creating new revisions.
* Visibility of current revision number in product listings, forms, and kanban views.

This module enables enhanced traceability and version control of products throughout their lifecycle.
