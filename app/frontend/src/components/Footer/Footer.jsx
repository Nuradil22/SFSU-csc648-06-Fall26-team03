import './Footer.css';

function Footer(){
    return(
        <footer className="footer">
            <div className="footer-column">
                <h1><span className="underline">    Footer c1   </span></h1>
                <p>This footer will look better later</p>
            </div>
            <div className="footer-column">
                <h1><span className="underline">    Footer c2   </span></h1>
                <p>This footer will look better later</p>
            </div>
            <div className="footer-column">
                <h1><span className="underline">Footer c3</span></h1>
                <p>This footer will look better later</p>
            </div>
        </footer>
    );
}

export default Footer;