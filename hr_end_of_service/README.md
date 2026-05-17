# HR End Of Service

A professional Odoo addon to calculate Saudi end of service benefits for employees.

## Features
- Creates a request record for end of service calculation.
- Computes service length from contract start date to termination date.
- Applies Saudi labor law conventions for entitlement days:
  - 21 days per year for the first 5 years.
  - 30 days per year after 5 years.
- Handles termination reasons such as employer termination, resignation, fixed-term end, mutual agreement and dismissal with cause.
- Calculates gross and net entitlement with optional deductions.

## Installation
1. Copy the module into the Odoo addons path.
2. Update the app list.
3. Install `HR End Of Service`.

## Notes
- Salary is taken from the employee contract when available.
- The module does not replace legal advice; it uses a common calculation model for Saudi end of service benefits.
