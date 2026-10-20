#!/usr/bin/env bash
# Reset the GitHub side of module 5 after a live demo, so the next session starts the same way.
#
#   1. If the demo merged the teammate's job into main, remove it again (through a pull request,
#      because main requires the checks to pass).
#   2. Recreate feature/weekly-department-report from main with the original change, Jane's email
#      included, so the next pull request fails the rule check again.
#
# Run from a clone of the repo, signed in to the gh CLI as the repo owner:
#   bash devops/instructor/reset_github_demo.sh
set -euo pipefail

REPO="christinasong97/fresh-market-dabs-lab"
BRANCH="feature/weekly-department-report"
SEED="demo/teammate-change"  # tag on the teammate's original commit
FILES=(
  resources/jobs/store_ops/so_weekly_department_report.job.yml
  src/store_ops/notebooks/department_report/publish_department_report.py
)

git fetch --quiet --tags origin

if git cat-file -e "origin/main:${FILES[0]}" 2>/dev/null; then
  echo "main has the teammate's job from the demo. Removing it through a pull request..."
  git switch --quiet -C demo-reset origin/main
  git rm --quiet "${FILES[@]}"
  git commit --quiet -m "Reset after the lab demo: remove the weekly department report job"
  git push --quiet --force origin demo-reset
  gh pr create --repo "$REPO" --base main --head demo-reset \
    --title "Reset after the lab demo" --body "Removes the teammate's job that was merged during the live demo."
  gh pr checks demo-reset --repo "$REPO" --watch
  gh pr merge demo-reset --repo "$REPO" --merge --delete-branch
  git fetch --quiet origin
fi

echo "Recreating $BRANCH from main with the original change..."
git switch --quiet -C "$BRANCH" origin/main
git checkout "$SEED" -- "${FILES[@]}"
git commit --quiet -m "Add weekly department report job"
git push --quiet --force origin "$BRANCH"
git switch --quiet -

echo "Done. Changes on $BRANCH compared with main:"
git diff --stat "origin/main...origin/$BRANCH"
