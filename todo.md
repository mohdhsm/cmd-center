# TODO List for Aramco Summary Features

## Modules to be implemented (General)

1. Dashboard module (current) (MVP Done))
2. The email connector. (needs to create database and sync layer)
3. Sharepoint workshop connector. 
4. Odoo connector.
5. implement Waha whatsapp connector.

## RUNNING OF NEXT 5 TODOS:

### Queue

- [ ] Create the database and sync function for the emails.
- [ ] the service layer to handle the send report button. 
- [ ] Create the send report button for overdue.
- [ ] create the send report button for stuck projects.
- [ ] create the send report button for order recieved.

### Done

- [x] implement and test the EMAIL connector. 
- [x] create the dashboard module. Main dashboard. 

## Overdue Summary - Future Enhancements

- [ ] Implement send report for overdue summary so the employee can change SSD.

## Stuck Summary - Future Enhancements

- [ ] Implement LLM blocking flag detection ("Waiting client", "Waiting internal", "External dependency")
- [ ] Implement LLM suggested next step generation
- [ ] Implement "Auto-create 'Update + next activity' tasks" button
- [ ] Implement "Send Email to owners" button
- [ ] implement send report to each owners

## Order Received Summary - Future Enhancements

- [ ] Add conversion rate calculation (requires stage transition history)
- [ ] Add "Approved in last 30d" metric (requires historical tracking)
- [ ] Identify and map custom field keys for:
  - [ ] Site contact number
  - [ ] PO/contract reference
  - [ ] Expected start/finish dates
  - [ ] Product type
  - [ ] Quantity
- [ ] Implement "Send to Aramco Reminder" button
- [ ] send report to owners. 

## General Enhancements

- [ ] Add export functionality (CSV/PDF) for summary reports
- [ ] Optimize database queries with proper indexes
- [ ] Add caching for frequently accessed summaries
- [ ] Implement historical trend tracking for metrics
