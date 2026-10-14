import { useState } from "react";

import './Roadmap.css';
import quotes from '../data/inspoQuotes.js';

const quoteCnt = quotes.length;

function getInspo(){
    let quoteIdx = Math.floor(Math.random() * quoteCnt);
    return quotes[quoteIdx];
}

let quote = getInspo();

function Roadmap({ darkMode }){
    
    const [isDragDrop, setIsDragDrop] = useState(false);

    return(
        <main> 
            <div className ="banner"> 
            <h1 className="banner-title">Build Your Dream</h1>
            <p>"{quote.line}"</p>
            <p>- {quote.cred}</p>
            </div>

            <div className ="res-body">
                <div className="ai-chat box">
                    <div className="chat-head">
                        <h1>AI Career Guidance</h1>
                    </div>
                    
                    <div className="chat-section">
                        <p>something something in the month of May</p>
                    </div>

                    <div className="chat-input">
                        <p>this is where the user types a message</p>
                    </div>

                </div>

                <div className="res-files box">
                    <h1>Your Documents</h1>
                    <p>--- example layout ---</p>
                    <h3>Job Category: Cyber Security</h3>
                    <ul className="docs">
                        <li><a href="" className="doc-link">cyber-security-resume.pdf</a></li>
                        <li><a href="" className="doc-link">OpenAI-cybersec-cover-letter.pdf</a></li>
                        <li><a href="" className="doc-link">Hive-cover-letter.pdf</a></li>
                    </ul>
                    <h3>Job Category: Embedded Systems</h3>
                    <ul className="docs">
                        <li><a href="" className="doc-link">embedded-systems-resume.pdf</a></li>
                        <li><a href="" className="doc-link">Apera-cover-letter.pdf</a></li>
                        <li><a href="" className="doc-link">General-Motor-cover-letter.pdf</a></li>
                    </ul>
                    <h3>Job Category: Software Development</h3>
                    <ul className="docs">
                        <li><a href="" className="doc-link">software-dev-resume.pdf</a></li>
                        <li><a href="" className="doc-link">software-dev-cover-letter.pdf</a></li>
                    </ul>
                </div>
            </div>
        </main>
    );
};

export default Roadmap;