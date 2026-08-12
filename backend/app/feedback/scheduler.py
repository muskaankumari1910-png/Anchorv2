"""
Sprint 9: Feedback Loop Scheduler

Automated background task that periodically:
1. Updates feedback examples from recent audit events
2. Tracks acceptance rate improvements
3. Maintains workspace-specific learning

This can be run as a cron job or background service.
"""
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.feedback.service import update_workspace_examples, track_improvements
from app.models import Requirement
from sqlalchemy import distinct

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_all_workspaces():
    """
    Update feedback examples for all active workspaces.
    
    Runs periodically (e.g., every hour) to collect new training data.
    """
    db = SessionLocal()
    
    try:
        logger.info("Starting feedback loop update for all workspaces...")
        
        # Get all active workspaces (workspaces with requirements)
        workspaces = db.query(distinct(Requirement.workspace_id)).all()
        workspace_ids = [w[0] for w in workspaces]
        
        logger.info(f"Found {len(workspace_ids)} active workspaces: {workspace_ids}")
        
        total_examples = 0
        
        for workspace_id in workspace_ids:
            try:
                # Update feedback examples
                count = update_workspace_examples(workspace_id, db)
                total_examples += count
                
                logger.info(f"Workspace {workspace_id}: {count} new examples")
                
                # Track improvements
                trends = track_improvements(workspace_id, db)
                
                logger.info(f"Workspace {workspace_id} metrics:")
                logger.info(f"  - Acceptance rate: {trends['acceptance_rate']}%")
                logger.info(f"  - Trend: {trends['trend']}")
                
                if trends['trend'] == 'improving':
                    logger.info(f"  🎉 Workspace {workspace_id} showing improvement!")
                elif trends['trend'] == 'declining':
                    logger.warning(f"  ⚠️  Workspace {workspace_id} acceptance rate declining")
                
            except Exception as e:
                logger.error(f"Failed to update workspace {workspace_id}: {e}")
        
        logger.info(f"Feedback loop update complete. Total new examples: {total_examples}")
        
        return {
            "workspaces_updated": len(workspace_ids),
            "total_examples": total_examples,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Feedback loop update failed: {e}")
        raise
    finally:
        db.close()


def run_feedback_scheduler():
    """
    Run the feedback scheduler once.
    
    This can be called from a cron job or similar scheduler.
    """
    try:
        result = asyncio.run(update_all_workspaces())
        print(f"Feedback update completed: {result}")
        return result
    except Exception as e:
        print(f"Feedback scheduler failed: {e}")
        return None


async def feedback_loop_daemon(interval_minutes: int = 60):
    """
    Run feedback loop continuously with specified interval.
    
    For use in production as a background service.
    """
    logger.info(f"Starting feedback loop daemon (interval: {interval_minutes} minutes)")
    
    while True:
        try:
            await update_all_workspaces()
            logger.info(f"Next update in {interval_minutes} minutes...")
            await asyncio.sleep(interval_minutes * 60)
            
        except KeyboardInterrupt:
            logger.info("Feedback loop daemon stopped by user")
            break
        except Exception as e:
            logger.error(f"Daemon error: {e}")
            logger.info(f"Retrying in {interval_minutes} minutes...")
            await asyncio.sleep(interval_minutes * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "daemon":
        # Run as daemon
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        asyncio.run(feedback_loop_daemon(interval))
    else:
        # Run once
        run_feedback_scheduler()