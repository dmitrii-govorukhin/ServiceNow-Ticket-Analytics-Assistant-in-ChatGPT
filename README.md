# ServiceNow Ticket Analytics Assistant in ChatGPT

**Project:**                   Leveraging ChatGPT's capabilities to ServiceNow Help Desk ticket analytics.

**Consumer:**                  Contra Costa County EHSD

**Program languages:**         Python

**Python libraries are used:** fastapi, uvicorn, pandas, openpyxl, duckdb, python-dotenv, pydantic

**Description:**               The Ticket Analytics Assistant is a  conversational analytics tool (custom ChatGPT) for ServiceNow ticketing data. It allows staff to query ticket statistics in plain English — no SQL, no filters, no dashboards — and receive instant, accurate answers. 

Example queries:
 - How many tickets are currently in progress for the T1 - Contra Costa - CalSAWS Help Desk group?
 - What is the average resolution time by assignment group?
 - How many tickets were resolved last week by employees?
________________________________________
*How It Works:*

The system follows a five-stage pipeline:

- User question (natural language)
- Custom ChatGPT — interprets intent, produces structured JSON query
- FastAPI backend — translates JSON into SQL
- DuckDB analytics engine — executes query against ticket history
- Custom ChatGPT — formats the result into a plain-English answer

ChatGPT plays two roles: Natural Language Interface (question → JSON) and Presentation Layer (JSON result → human-readable answer). All analytics logic runs in the backend.
________________________________________
*Data Source:*

A custom ServiceNow table exports ticket history to Excel spreadsheet. Each row records a change in one of three tracked fields:

 - Status	→ Lifecycle stage of the ticket
 - Assigned to → Employee currently responsible
 - Assignment group	→ Team currently responsible

This history is refreshed on demand by a separate script.
________________________________________
*Supported Metrics:*

 - total_tickets →	All unique tickets (current state)
 - resolved_tickets →	Tickets currently in Resolved status
 - closed_tickets →	Tickets currently in Closed status
 - tickets_in_progress → Tickets actively being worked on (excludes New, Resolved, Closed, Cancelled)
 - avg_resolution_time →	Average time from creation to resolution, in minutes

All metrics support filtering by assignment group, assignee, and date range. Most support group_by for breakdowns. The filter_scope parameter controls whether filters apply to the ticket's current state, its state at resolution, or any point in its history.
________________________________________

The repository contains the backend files.

**Results / Key Findings:** This custom ChatGPT allows authorized users to instantly access the statistics they need for help desk tickets in ServiceNow without having to create or run reports. ChatGPT's advanced capabilities allow it to respond to any user prompt, and the instructions clearly specify when it needs to access the backend service to retrieve the ServiceNow statistics data.

**Illustration:** Custom ChatGPT demo video

[![Watch the video]]([https://youtu.be/T-D1KVIuvjA](https://github.com/dmitrii-govorukhin/ServiceNow-Ticket-Analytics-Assistant-in-ChatGPT/blob/main/Custom%20ChatGPT%20Demo.mp4))
