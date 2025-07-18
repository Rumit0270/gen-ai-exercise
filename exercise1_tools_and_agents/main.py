
import os
import asyncio
import asyncpg
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import PydanticOutputParser

load_dotenv()

LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# PostgreSQL configuration
PG_DB = os.environ.get("POSTGRES_DB", "company")
PG_HOST = os.environ.get("POSTGRES_HOST", "localhost")
PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
PG_USER = os.environ.get("POSTGRES_USER", "postgres")
PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")

DATABASE_CONFIG = {
    "host": PG_HOST,
    "port": PG_PORT,
    "database": PG_DB,
    "user": PG_USER,
    "password": PG_PASSWORD
}

# Create Pydantic models for structured data
class CompanyInfo(BaseModel):
    """Model for extracted company information"""
    company_name: str = Field(description="The full name of the company")
    founding_date: str = Field(description="The founding date of the company")
    founders: List[str] = Field(description="List of founders' names")

class ExtractedCompanies(BaseModel):
    """Model for all extracted companies"""
    companies: List[CompanyInfo] = Field(description="List of extracted company information")


async def insert_companies_to_db(companies: List[CompanyInfo]) -> bool:
    """
    Function that takes a list of company info and inserts into Postgres db
    """
    try:
        # Create connection
        conn = await asyncpg.connect(**DATABASE_CONFIG)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS company_details (
                id SERIAL PRIMARY KEY,
                company_name VARCHAR(255) NOT NULL,
                founded_in DATE NOT NULL,
                founded_by TEXT[] NOT NULL
            );
        """)
        
        for company in companies:
            # Convert string date to date object
            date_obj = datetime.strptime(company.founding_date, "%Y-%m-%d").date()
            
            await conn.execute("""
                INSERT INTO company_details (company_name, founded_in, founded_by)
                VALUES ($1, $2, $3)
            """, company.company_name, date_obj, company.founders)
        
        await conn.close()
        print(f"Successfully inserted {len(companies)} companies into database")
        return True
        
    except Exception as e:
        print(f"Error inserting companies: {e}")
        return False

async def get_stored_companies() -> List[Dict]:
    """
    Helper function to retrieve stored companies from database
    """
    try:
        conn = await asyncpg.connect(**DATABASE_CONFIG)
        
        rows = await conn.fetch("""
            SELECT id, company_name, founded_in, founded_by
            FROM company_details
            ORDER BY founded_in
        """)
        
        await conn.close()
        
        # Convert to list of dictionaries
        companies = []
        for row in rows:
            companies.append({
                'id': row['id'],
                'company_name': row['company_name'],
                'founded_in': row['founded_in'],
                'founded_by': row['founded_by']
            })
        
        return companies
        
    except Exception as e:
        print(f"Error retrieving companies: {e}")
        return []

def create_extraction_chain(llm):
    """
    Create LCEL chain for company extraction
    """
    # Setup parser
    parser = PydanticOutputParser(pydantic_object=ExtractedCompanies)
    
    # Create prompt template
    prompt_template = """
    Extract company information from the following text. For each company mentioned, identify:
    1. Company name (full official name)
    2. Founding date (The date the company was founded, in YYYY-MM-DD format)
    3. Founders (list of individual founder names)
    
    **IMPORTANT**: In certain scenarios, the founding date information may not be available. To handle such cases: 
      - If only the year is provided, default the date to **January 1st** of that year.
      - If the year and month are provided, default the date to the **1st day** of the specified month. 
      - If you cannot deduce the date, DO NOT include that company in the output.
    
    Text to analyze: ```{text}```
    
    Output format Instruction: ```{format_instructions}```
    """
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["text"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
        
    # Create LCEL chain
    extraction_chain = (
        {"text": RunnablePassthrough()}
        | prompt
        | llm
        | parser
    )
    
    return extraction_chain

async def extract_and_store_companies(essay_text: str, openai_api_key: str) -> List[Dict]:
    """
    Function that takes an essay and extracts company info, then inserts into PG.
    """
    try:
        llm = ChatOpenAI(
            model=LLM_MODEL,
            temperature=0,
            openai_api_key=openai_api_key
        )
        
        # Create LCEL extraction chain
        extraction_chain = create_extraction_chain(llm)
        
        # Split essay into paragraphs for better processing
        paragraphs = [p.strip() for p in essay_text.split('\n\n') if p.strip()]
        
        all_companies = []
        
        # Process each paragraph using LCEL
        for i, paragraph in enumerate(paragraphs):
            try:
                result = await extraction_chain.ainvoke(paragraph)
                
                for company in result.companies:
                    all_companies.append(company)
                    print(f"Found: {company.company_name} ({company.founding_date})")
            
            except Exception as e:
                print(f"Error processing paragraph: {e}")
                continue
        
        print(f"\n Total companies extracted: {len(all_companies)}")
        
        if all_companies:
            success = await insert_companies_to_db(all_companies)
            
            if success:
                stored_companies = await get_stored_companies()
                return stored_companies
        
        return []
        
    except Exception as e:
        print(f"Error in extraction and storage: {e}")
        return []

async def main():
    # Sample essay text containing company information
    essay_text = """
    In the ever-evolving landscape of global commerce, the origin stories of major corporations are not merely tales of personal ambition and entrepreneurial spirit but also reflections of broader socio-economic trends and technological revolutions that have reshaped industries. These narratives, which often begin with modest ambitions, unfold into chronicles of innovation and strategic foresight that define industries and set benchmarks for future enterprises. 

    Early Foundations: Pioneers of Industry 

    One of the earliest examples is The Coca-Cola Company, founded on May 8, 1886, by Dr. John Stith Pemberton in Atlanta, Georgia. Initially sold at Jacob's Pharmacy as a medicinal beverage, Coca-Cola would become one of the most recognized brands worldwide, revolutionizing the beverage industry. Similarly, Sony Corporation was established on May 7, 1946, by Masaru Ibuka and Akio Morita in Tokyo, Japan. Starting with repairing and building electrical equipment in post-war Japan, Sony would grow to pioneer electronics, entertainment, and technology. 

    As the mid-20th century progressed, McDonald’s Corporation emerged as a game-changer in the fast-food industry. Founded on April 15, 1955, in Des Plaines, Illinois, by Ray Kroc, McDonald’s built upon the original concept of Richard and Maurice McDonald to standardize and scale fast-food service globally. Around the same period, Intel Corporation was established on July 18, 1968, by Robert Noyce and Gordon Moore in Mountain View, California, driving advancements in semiconductors and microprocessors that became the backbone of modern computing. 

    The Rise of Technology Titans 

    Samsung Electronics Co., Ltd., founded on January 13, 1969, by Lee Byung-chul in Su-dong, South Korea, initially focused on producing electrical appliances like televisions and refrigerators. As Samsung expanded into semiconductors, telecommunications, and digital media, it grew into a global technology leader. Similarly, Microsoft Corporation was founded on April 4, 1975, by Bill Gates and Paul Allen in Albuquerque, New Mexico, with the vision of placing a computer on every desk and in every home. 

    In Cupertino, California, Apple Inc. was born on April 1, 1976, founded by Steve Jobs, Steve Wozniak, and Ronald Wayne. Their mission to make personal computing accessible and elegant revolutionized technology and design. A few years later, Oracle Corporation was established on June 16, 1977, by Larry Ellison, Bob Miner, and Ed Oates in Santa Clara, California. Specializing in relational databases, Oracle would become a cornerstone of enterprise software and cloud computing. 

    NVIDIA Corporation, founded on April 5, 1993, by Jensen Huang, Chris Malachowsky, and Curtis Priem in Santa Clara, California, began with a focus on graphics processing units (GPUs) for gaming. Today, NVIDIA is a leader in artificial intelligence, deep learning, and autonomous systems, showcasing the power of continuous innovation. 

    E-Commerce and the Internet Revolution 

    The 1990s witnessed a dramatic shift toward e-commerce and internet technologies. Amazon.com Inc. was founded on July 5, 1994, by Jeff Bezos in a garage in Bellevue, Washington, with the vision of becoming the world’s largest online bookstore. This vision rapidly expanded to encompass e-commerce, cloud computing, and digital streaming. Similarly, Google LLC was founded on September 4, 1998, by Larry Page and Sergey Brin, PhD students at Stanford University, in a garage in Menlo Park, California. Google’s mission to “organize the world’s information” transformed how we search, learn, and connect. 

    In Asia, Alibaba Group Holding Limited was founded on June 28, 1999, by Jack Ma and 18 colleagues in Hangzhou, China. Originally an e-commerce platform connecting manufacturers with buyers, Alibaba expanded into cloud computing, digital entertainment, and financial technology, becoming a global powerhouse. 

    In Europe, SAP SE was founded on April 1, 1972, by Dietmar Hopp, Hans-Werner Hector, Hasso Plattner, Klaus Tschira, and Claus Wellenreuther in Weinheim, Germany. Specializing in enterprise resource planning (ERP) software, SAP revolutionized how businesses manage operations and data. 

    Social Media and Digital Platforms 

    The 2000s brought a wave of social media and digital platforms that reshaped communication and commerce. LinkedIn Corporation was founded on December 28, 2002, by Reid Hoffman and a team from PayPal and Socialnet.com in Mountain View, California, focusing on professional networking. Facebook, Inc. (now Meta Platforms, Inc.) was launched on February 4, 2004, by Mark Zuckerberg and his college roommates in Cambridge, Massachusetts, evolving into a global social networking behemoth. 

    Another transformative platform, Twitter, Inc., was founded on March 21, 2006, by Jack Dorsey, Biz Stone, and Evan Williams in San Francisco, California. Starting as a microblogging service, Twitter became a critical tool for communication and social commentary. Spotify AB, founded on April 23, 2006, by Daniel Ek and Martin Lorentzon in Stockholm, Sweden, leveraged streaming technology to democratize music consumption, fundamentally altering the music industry. 

    In the realm of video-sharing, YouTube LLC was founded on February 14, 2005, by Steve Chen, Chad Hurley, and Jawed Karim in San Mateo, California. YouTube became the leading platform for user-generated video content, influencing global culture and media consumption. 

    Innovators in Modern Technology 

    Tesla, Inc., founded on July 1, 2003, by a group including Elon Musk, Martin Eberhard, Marc Tarpenning, JB Straubel, and Ian Wright, in San Carlos, California, championed the transition to sustainable energy with its electric vehicles and energy solutions. Airbnb, Inc., founded in August 2008 by Brian Chesky, Joe Gebbia, and Nathan Blecharczyk in San Francisco, California, disrupted traditional hospitality with its peer-to-peer lodging platform. 

    In the realm of fintech, PayPal Holdings, Inc. was established in December 1998 by Peter Thiel, Max Levchin, Luke Nosek, and Ken Howery in Palo Alto, California. Originally a cryptography company, PayPal became a global leader in online payments. Stripe, Inc., founded in 2010 by Patrick and John Collison in Palo Alto, California, followed suit, simplifying online payments and enabling digital commerce. 

    Square, Inc. (now Block, Inc.), founded on February 20, 2009, by Jack Dorsey and Jim McKelvey in San Francisco, California, revolutionized mobile payment systems with its simple and accessible card readers. 

    Recent Disruptors 

    Zoom Video Communications, Inc. was founded on April 21, 2011, by Eric Yuan in San Jose, California. Initially designed for video conferencing, Zoom became essential during the COVID-19 pandemic, transforming remote work and communication. Slack Technologies, LLC, founded in 2009 by Stewart Butterfield, Eric Costello, Cal Henderson, and Serguei Mourachov in Vancouver, Canada, redefined workplace communication with its innovative messaging platform. 

    Rivian Automotive, Inc., founded on June 23, 2009, by RJ Scaringe in Plymouth, Michigan, entered the electric vehicle market with a focus on adventure and sustainability. SpaceX, established on March 14, 2002, by Elon Musk in Hawthorne, California, revolutionized aerospace with reusable rockets and ambitious plans for Mars exploration. 

    TikTok, developed by ByteDance and launched in September 2016 by Zhang Yiming in Beijing, China, revolutionized short-form video content, becoming a cultural phenomenon worldwide. 

    Conclusion 

    These corporations, with their diverse beginnings and visionary founders, exemplify the interplay of innovation, timing, and strategic foresight that shapes industries and transforms markets. From repairing electronics in post-war Japan to building global e-commerce empires and redefining space exploration, their stories are milestones in the narrative of global economic transformation. Each reflects not only the aspirations of their founders but also the technological advancements and socio-economic trends of their time, serving as inspirations for future innovators.
    """
    
    # Run the main extraction and storage process
    stored_companies = await extract_and_store_companies(essay_text, OPENAI_API_KEY)
    
    # Display results
    if stored_companies:
        print("\n Final Results in Database:")
        print(f"Number of companies stored: {len(stored_companies)}")
    else:
        print("No companies were successfully stored")


if __name__ == "__main__":
    asyncio.run(main())