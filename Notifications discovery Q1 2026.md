
## Part 1: what excites teams, what concerns them, what questions do they have about a new breaking news tool?

**People are excited by the idea of new alerts tooling:** They see a streamlined process of sending breaking news alerts as a way to have stronger control over reader relationships. Being able to  drive direct traffic  more easily is a strategic priority. There's an appetite to use alerts as a gateway to newsletters and subscription revenue.

**Current process pain:** Sending alerts today is slow, fragmented, and stressful. Email takes \~20 minutes to train someone on; app alerts take 5; more if people send test alerts, which some do because they are not confident the tool will work . Staff juggle Braze (clunky, risky access), Apple News (limited to 5/day, hard access), and multiple platforms with no unified view. Headlines change mid-send, previews are inconsistent, and there's real fear of typos, wrong links, duplicate sends, or targeting the wrong region.

**What needs solving:** Speed and confidence. Teams want one tool that sends to all channels, previews reliably across formats (especially mobile email), **and has smart guardrails to prevent mistakes**. They need clarity on thresholds (what counts as breaking?), regional consistency, better test workflows, and a way to signal story updates without spamming. Training and access control matter \- and most crucially people want to feel “safe” when sending alerts.

**Open questions:** Can subject lines auto-populate? Will it handle liveblog blocks? Can you send to multiple regions at once, or customize per audience? What about corrections, columnists, or non-breaking "exclusive" sends? How do you track satisfaction, not just clicks? And critically: can a short-term fix ship fast without blocking the long-term unified solution?

## Part 2: what would you need to have/see in order to be comfortable with a productionised working breaking news prototype?

V1 Breaking News Prototype: Sign-off Requirements by popularity

**Preview and testing capability (7): confidence in tooling**  
Preview notifications/emails  
Images  
Subject/preheader rendering  
test on dev  
general testing

**Access control and permissions management (4)**

Who can send  
Controlled access  
Permission workflows,   
Training required before access.

**Tracking and monitoring (4)**

 audit log of who sent what/when, delivery confirmation, general tracking, UTM usage.

**Subject line customization (3) –** 

remove 100-char limit; edit/remove “Breaking News”; variable subjects with standard preheaders.

**Vulnerability and security assessment (3) –** 

dependency checks; security/vulnerability review.

Schedule/intelligent timing handling (3) – intelligent timing not needed; avoid mistakes; handle updates for scheduled sends.

**Performance and speed (3) –** 

as fast or faster than current tools; meets best-practice benchmarks.

**API capability (2) –** 

trigger sends via API; avoid manual Braze steps.

**Support and maintenance (2) –** 

ownership for bugs/outages; 24/7 coverage.

**Live blog integration (2) –** 

target specific live-blog posts.

**Opt-out functionality (2) –**

 easy opt-out; opt out of specific categories.

**Duplicate and send detection (2) –** 

user frequency/duplication checks; detect if link already sent.

**Simpler interface (2) –** 

fewer steps; simpler than Braze.

**Training process (1)**

**Backup/fallback plan (1)**

**Legal terms compliance (Braze T\&Cs) (1)**

**Send corrections capability (1)**

**Composer integration (1)**

**Email/notification independence (1)**

**Braze session management (1)**

**Preheader field addition (1)**

**Image replacement ease (1)**