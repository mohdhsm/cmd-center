# TODO List for Aramco Summary Features

## Overdue Summary - Future Enhancements

- [ ] Implement "Create tasks for all Due Soon (7d) without next activity" button
- [ ] Implement "Message PMs with top 3 overdue each" button
- [ ] Implement "Send to Aramco" button

## Stuck Summary - Future Enhancements

- [ ] Add recovery rate calculation (requires stage_change_time tracking)
- [ ] Implement LLM blocking flag detection ("Waiting client", "Waiting internal", "External dependency")
- [ ] Implement LLM suggested next step generation
- [ ] Implement "Auto-create 'Update + next activity' tasks" button
- [ ] Implement "Send Email to owners" button

## Order Received Summary - Future Enhancements

- [ ] Add conversion rate calculation (requires stage transition history)
- [ ] Add "Approved in last 30d" metric (requires historical tracking)
- [ ] Identify and map custom field keys for:
  - [ ] Site contact number
  - [ ] PO/contract reference
  - [ ] Expected start/finish dates
  - [ ] Product type
  - [ ] Quantity
- [ ] Implement "Create 'Identify end user + book call' tasks" button
- [ ] Implement "Draft email/WhatsApp template" button
- [ ] Implement "Send to Aramco Reminder" button

## General Enhancements

- [ ] Add export functionality (CSV/PDF) for summary reports
- [ ] Add email scheduling for automated summary reports
- [ ] Optimize database queries with proper indexes
- [ ] Add caching for frequently accessed summaries
- [ ] Implement historical trend tracking for metrics

## Technical Debt

- [ ] Add unit tests for `aramco_summary_service.py`
- [ ] Add integration tests for summary API endpoints
- [ ] Add error handling for edge cases (no deals, missing data)
- [ ] Add logging for performance monitoring
- [ ] Document custom field extraction process
