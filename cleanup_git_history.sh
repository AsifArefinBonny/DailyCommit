#!/bin/bash
# Git History Cleanup Script
# This script removes files containing secrets from git history

set -e  # Exit on error

echo "🚨 GIT HISTORY CLEANUP - REMOVING SECRETS"
echo "========================================"
echo ""
echo "⚠️  WARNING: This will rewrite git history!"
echo "⚠️  This requires force-push to GitHub!"
echo "⚠️  Make sure you have rotated credentials first!"
echo ""
read -p "Have you rotated the Telegram bot token? (yes/no): " rotated
if [ "$rotated" != "yes" ]; then
    echo "❌ Please rotate credentials first! See URGENT_ACTIONS_REQUIRED.md"
    exit 1
fi

echo ""
echo "Creating backup branch..."
git branch backup-before-history-clean || echo "Backup branch may already exist"

echo ""
echo "Files to be removed from history:"
cat << 'FILELIST'
verify_migration.py
run_migration.py  
run_migration_direct.py
apply_migration.py
check_lesson_status.py
ux_audit_framework.py
comprehensive_iterative_test.py
automated_bot_test.py
comprehensive_fix_test.py
test_webhook_direct.py
test_question_flow.py
final_comprehensive_test.py
comprehensive_test.py
get_chatid.py
test_bot.py
bot/generate_lesson.py
FILELIST

echo ""
read -p "Proceed with history cleanup? (yes/no): " proceed
if [ "$proceed" != "yes" ]; then
    echo "❌ Cancelled"
    exit 1
fi

echo ""
echo "Running git-filter-repo to remove sensitive files..."

git filter-repo --invert-paths \
  --path verify_migration.py \
  --path run_migration.py \
  --path run_migration_direct.py \
  --path apply_migration.py \
  --path check_lesson_status.py \
  --path ux_audit_framework.py \
  --path comprehensive_iterative_test.py \
  --path automated_bot_test.py \
  --path comprehensive_fix_test.py \
  --path test_webhook_direct.py \
  --path test_question_flow.py \
  --path final_comprehensive_test.py \
  --path comprehensive_test.py \
  --path get_chatid.py \
  --path test_bot.py \
  --path bot/generate_lesson.py \
  --force

echo ""
echo "✅ Git history cleaned!"
echo ""
echo "⚠️  NEXT STEPS:"
echo "1. Review the changes:"
echo "   git log --oneline --graph --all"
echo ""
echo "2. Force push to GitHub:"
echo "   git remote add origin git@github.com:AsifArefinBonny/DailyCommit.git"
echo "   git push origin --force --all"
echo "   git push origin --force --tags"
echo ""
echo "3. Verify secrets are gone:"
echo "   git log -S 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9' --all"
echo "   (Should return no results)"
echo ""
echo "4. Ask collaborators to re-clone the repository"
echo ""
