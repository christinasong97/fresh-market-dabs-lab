# Pre-work email (send 3 to 5 days before the lab)

**Subject:** Before our CI/CD with Declarative Automation Bundles lab: 15 minutes of setup

Hi everyone,

Thanks for joining the **CI/CD with Declarative Automation Bundles** lab on **[date, time]**. To make the most of
our 90 minutes, please do this setup beforehand. It takes about 15 minutes, and most of that is waiting.

**1. Sign up for Databricks Free Edition (5 minutes)**
- Go to https://www.databricks.com/learn/free-edition and click **Sign up**.
- Sign in with your email, Google, or Microsoft account. You get your own workspace, free.
- If your work email doesn't work, use a personal email. The lab uses only made-up data.

**2. Create your lab folder (2 minutes)**
- In your workspace, click **Workspace** in the left sidebar, then **Create → Git folder**.
- Paste this URL and click **Create**: `https://github.com/christinasong97/fresh-market-dabs-lab`
- No GitHub account is needed.

**3. Run the setup notebook (about 5 minutes, mostly waiting)**
- In your new folder, open **`00_START_HERE`**.
- At the top, set compute to **Serverless**, then click **Run all**.
- When it finishes, every line under **Step 2 · Check your environment** should show ✅.

**4. Reply to this email if anything doesn't show ✅**, with a screenshot of the error. We'll sort it out before the
lab, so nobody loses time on the day.

Please don't start the modules in the `lab` folder yet; we'll do those together.

**What to expect:** you'll take a job built by hand, turn it into code with Genie Code, test your own copy, and see
how a change gets to production through a pull request, automated checks, and an approval. Everything happens in
the Databricks workspace: no terminal, no installs.

See you on [date]!

[Your name]

---

## Instructor notes (don't send)

- **Before sending:** have one attendee from the customer try step 1 with their **work email** at least a week
  ahead. If work emails can't sign up, update step 1 to say "use a personal email."
- **Track replies:** anyone who didn't reply ✅ the day before gets a quick check-in. The most common problems will be
  sign-up and the daily usage limit (if someone runs the setup many times).
- **On the day:** attendees who skipped pre-work can still do steps 1 to 3 in the first 10 minutes, while you cover
  "Today vs. target." Setup runs in the background.
- **Between rehearsals:** run `devops/instructor/reset_demo` in your demo workspace to get back to the start of
  module 1 without a new account.
