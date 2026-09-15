import { useState } from "react";

import './Resume.css';
import quotes from '../data/inspoQuotes.js';

const quoteCnt = quotes.length;

function getInspo(){
    let quoteIdx = Math.floor(Math.random() * quoteCnt);
    return quotes[quoteIdx];
}

let quote = getInspo();

function Resume({ darkMode }){
    
    const [isDragDrop, setIsDragDrop] = useState(false);

    return(
        <main> 
            <div className ="banner"> 
            <h1 className="banner-title">Build Your Resume</h1>
            <p>"{quote.line}"</p>
            <p>- {quote.cred}</p>
            </div>

            <div className ="resBody">
                <div className="resWorkArea box">
                    <div className="toggle-section">

                        <h2 className={isDragDrop ? "toggle-option" : "toggle-option option-toggled"}>Upload Resume</h2>

                        <button
                            className={`toggle ${isDragDrop ? "on" : ""}`}
                            onClick={() => setIsDragDrop(!isDragDrop)}
                            aria-pressed={isDragDrop}
                        >
                            <span className="toggle-knob"></span>
                        </button>

                        <h2 className={isDragDrop ? "toggle-option option-toggled" : "toggle-option"}>Build Resume</h2>
                    </div>

                    <div className={isDragDrop ? "zone-off" : "dragDropZone"}>
                        <h1>Drag and Drop your .pdf or .docs here!</h1>
                        <h3>...or click to browse for file</h3>
                    </div>

                </div>

                <div className="resFiles box">
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

export default Resume;