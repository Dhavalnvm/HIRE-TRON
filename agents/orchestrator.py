"""
Orchestrator Agent
Coordinates all agents and manages workflow
"""

import asyncio
import logging
from typing import Dict, List, Optional
from agents.jd_parser import JDParserAgent
from agents.resume_screener import ResumeScreenerAgent
from agents.sourcing_agent import SourcingAgent
from agents.compensation_agent import CompensationAgent
from agents.offer_agent import OfferAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Orchestrate multi-agent recruitment workflow"""
    
    def __init__(self):
        """Initialize all agents"""
        self.jd_parser = JDParserAgent()
        self.resume_screener = ResumeScreenerAgent()
        self.sourcing_agent = SourcingAgent()
        self.compensation_agent = CompensationAgent()
        self.offer_agent = OfferAgent()
        logger.info("Orchestrator initialized with all agents")
    
    async def parse_jd_async(self, jd_text: str) -> Optional[Dict]:
        """Async wrapper for JD parsing"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.jd_parser.parse,
            jd_text
        )
    
    async def screen_resume_async(
        self,
        jd_text: str,
        resume_text: str,
        parsed_jd: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Async wrapper for resume screening"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.resume_screener.screen,
            jd_text,
            resume_text,
            parsed_jd
        )
    
    async def generate_sourcing_async(
        self,
        jd_text: str,
        parsed_jd: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Async wrapper for sourcing strategy"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.sourcing_agent.generate_strategy,
            jd_text,
            parsed_jd
        )
    
    async def generate_compensation_async(
        self,
        jd_text: str,
        parsed_jd: Optional[Dict] = None,
        candidate_score: Optional[int] = None
    ) -> Optional[Dict]:
        """Async wrapper for compensation suggestion"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.compensation_agent.suggest_compensation,
            jd_text,
            parsed_jd,
            candidate_score
        )
    
    async def screen_multiple_candidates(
        self,
        jd_text: str,
        candidates: List[Dict],
        parsed_jd: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Screen multiple candidates concurrently
        
        Args:
            jd_text: Job description text
            candidates: List of candidate dictionaries
            parsed_jd: Optional parsed JD
            
        Returns:
            List of screening results
        """
        tasks = []
        for candidate in candidates:
            task = self.screen_resume_async(
                jd_text,
                candidate['resume_text'],
                parsed_jd
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results with candidate info
        enriched_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Screening failed for candidate {i}: {result}")
                continue
            
            if result:
                enriched_results.append({
                    **candidates[i],
                    'screening': result
                })
        
        return enriched_results
    
    async def full_analysis(
        self,
        jd_text: str
    ) -> Dict:
        """
        Run full job analysis (parsing, sourcing, compensation) concurrently
        
        Args:
            jd_text: Job description text
            
        Returns:
            Combined analysis results
        """
        try:
            # Run parsing first
            parsed_jd = await self.parse_jd_async(jd_text)
            
            # Run sourcing and compensation concurrently
            sourcing_task = self.generate_sourcing_async(jd_text, parsed_jd)
            compensation_task = self.generate_compensation_async(jd_text, parsed_jd)
            
            sourcing, compensation = await asyncio.gather(
                sourcing_task,
                compensation_task,
                return_exceptions=True
            )
            
            return {
                'parsed_jd': parsed_jd,
                'sourcing': sourcing if not isinstance(sourcing, Exception) else None,
                'compensation': compensation if not isinstance(compensation, Exception) else None
            }
            
        except Exception as e:
            logger.error(f"Error in full analysis: {e}")
            return {}
    
    def generate_offer_letter_sync(
        self,
        candidate_name: str,
        job_title: str,
        company_name: str,
        salary: int,
        start_date: str,
        parsed_jd: Optional[Dict] = None,
        additional_details: Optional[Dict] = None
    ) -> Optional[str]:
        """Generate offer letter (synchronous)"""
        return self.offer_agent.generate_offer_letter(
            candidate_name=candidate_name,
            job_title=job_title,
            company_name=company_name,
            salary=salary,
            start_date=start_date,
            parsed_jd=parsed_jd,
            additional_details=additional_details
        )