# TODO List for Aramco Summary Features

## Modules to be implemented (General)

1. Dashboard module (current) (MVP Done))
2. The email connector. (needs to create database and sync layer)
3. Sharepoint workshop connector. 
4. Odoo connector.
5. implement Waha whatsapp connector.
6. The export module. (To export to CSV or PDF report)

## RUNNING OF NEXT 5 TODOS:

### Queue

- [ ] fix the bug in cashflow araco page, the expected SAR is not showing any values
- [ ] Create the Aramco pagss (stuck, order, overdue) wire the ADD NOTE button.
- [ ] In Aramco pages (Stuch, order, overdue) enable the GET SUMMARY button for the each one (deals)
- [ ] go back to fix the dashboard information.
- [ ] create the send remindre functionality using email.
- [ ] fix the logs issues, when adding logs its not appearing. 
- [ ] Check the database items to see what is happening. 


-
### Done

- [x] Wire the "Send follow up reminders" to send reminder to each owner by email.
- [x] implement and test the EMAIL connector. 
- [x] create the dashboard module. Main dashboard. 
- [x] Create the database and sync function for the emails.
- [x] the service layer to handle the send report button. 

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
