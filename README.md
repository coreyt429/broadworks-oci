# broadworks-oci
This is the fourth iteration of my broadworks oci interface.


- v1: perl based, very kludgy, but worked
- v2: python port of perl code
- v3:
  - added object structure with Oci, Response, Enterprise, Group, and User objects
  - attempted to snake case everything, and constantly converting back to camel Case
  - recently added a test concept of reordering out of order parameters based on the
  - schema, which is what led to this project.

All of these have been useful over the last 17 years of work, and this version won't
stray to far from their original intent. Also needs to plug into my existing code
relatively easily.

Goals:
  - Be more schema driven.
  - map snake_case to camelCase instead of converting on the fly
  - tighter, more consistent object structure
  - learn something new
  - separate serverinfo code, and just let this be the oci interface
    we can put another layer in for managing multiple clusters.

    
