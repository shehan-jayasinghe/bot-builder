import "./landing-page.css";

const features = [
  ["✣", "Visual Agent Builder", "Design agents with reusable capabilities, prompts and tools."],
  ["▣", "Knowledge Base", "Connect documents, websites and business knowledge."],
  ["⌘", "Workflow Orchestration", "Build multi-step, multi-agent workflows with clear control."],
  ["◇", "Integrations", "Connect your existing APIs, tools and business systems."],
  ["◫", "Multi-Channel", "Deploy across web, messaging and support channels."],
  ["▥", "Monitoring & Analytics", "Track traces, performance, quality and evaluations."],
  ["⬡", "Governance & Compliance", "Apply safety, governance and access controls."],
  ["◎", "Multi-Tenant", "Support multiple organizations with secure isolation."],
] as const;

const useCases = [
  ["🛍", "Retail & E-commerce", "Product support, order journeys and personalized recommendations."],
  ["🏦", "Banking & Financial Services", "Customer onboarding, account support and controlled payment workflows."],
  ["🎧", "Customer Support", "Automate answers, process tickets and escalate when needed."],
  ["🏢", "Internal Operations", "Create AI assistants for knowledge, HR and operational workflows."],
] as const;

export default function HomePage() {
  return (
    <div className="landing">
      <header className="nav shell">
        <a href="#top" className="brand">
          <img src="/brand/agentforge-logo.svg" alt="AgentForge" />
        </a>
        <nav>
          <a href="#platform">Product</a>
          <a href="#features">Features</a>
          <a href="#solutions">Solutions</a>
          <a href="#how">How it works</a>
        </nav>
        <div className="navActions">
          <a className="textBtn" href="/signin">
            Sign in
          </a>
          <a className="button small" href="/signup">
            Get started →
          </a>
        </div>
      </header>

      <main id="top">
        <section className="hero shell">
          <div className="heroCopy">
            <div className="eyebrow">YOUR ORGANIZATION&apos;S AI WORKFORCE BUILDER</div>
            <h1>
              Build Smarter
              <br />
              Teams <span>with AI</span>
            </h1>
            <p>
              Create, connect and deploy AI agents that understand your business, work with your
              tools, and deliver real impact — all in one platform.
            </p>
            <div className="heroActions">
              <a className="button" href="/signup">
                Get started →
              </a>
              <a className="secondary" href="#platform">
                ▶ Explore platform
              </a>
            </div>
            <div className="proof">
              <span>⚡ Deploy in minutes</span>
              <span>♢ Enterprise ready</span>
              <span>♙ Built for teams</span>
            </div>
          </div>
          <div className="heroVisual">
            <div className="glow" />
            <img src="/brand/agent-hero.svg" alt="AI agent illustration" />
          </div>
        </section>

        <section className="trusted">
          <div className="shell">
            <span>BUILT FOR MODERN TEAMS</span>
            <div className="logos">
              <b>Customer Support</b>
              <b>Sales</b>
              <b>Operations</b>
              <b>Finance</b>
              <b>Commerce</b>
            </div>
          </div>
        </section>

        <section className="platform shell section" id="platform">
          <div className="sectionCopy">
            <div className="eyebrow">WHAT IS AGENTFORGE?</div>
            <h2>The complete platform for building AI agents</h2>
            <p>
              Design, orchestrate and manage AI agents securely at scale. Connect your data,
              automate workflows, evaluate behavior and deploy to the channels your customers
              already use.
            </p>
            <a className="button" href="/signup">
              Explore the platform →
            </a>
          </div>
          <div className="dashboard">
            <div className="dashTop">
              <b>AgentForge</b>
              <span>Agents</span>
              <button type="button">+ Create Agent</button>
            </div>
            <div className="stats">
              <div>
                <b>12</b>
                <span>Active agents</span>
              </div>
              <div>
                <b>8</b>
                <span>Workflows</span>
              </div>
              <div>
                <b>24.5K</b>
                <span>Conversations</span>
              </div>
              <div>
                <b>99.9%</b>
                <span>Uptime</span>
              </div>
            </div>
            <div className="agentRows">
              <p>
                <b>Customer Support</b>
                <span>Support</span>
                <i>● Online</i>
              </p>
              <p>
                <b>Sales Assistant</b>
                <span>Sales</span>
                <i>● Online</i>
              </p>
              <p>
                <b>Onboarding Agent</b>
                <span>Operations</span>
                <i>● Online</i>
              </p>
              <p>
                <b>Payment Collection</b>
                <span>Finance</span>
                <i>● Online</i>
              </p>
            </div>
          </div>
        </section>

        <section className="outcomes">
          <div className="shell outcomeInner">
            <div>
              <div className="eyebrow light">TURN YOUR IDEAS INTO ACTION</div>
              <h2>
                From knowledge
                <br />
                to real outcomes
              </h2>
              <p>
                Connect your data, tools and people. Let your AI agents handle the work while your
                team stays in control.
              </p>
            </div>
            <div className="flow">
              <div>Your Data</div>
              <b>→</b>
              <div>AI Agents</div>
              <b>→</b>
              <div>Your Tools</div>
              <b>→</b>
              <div>Real Impact</div>
            </div>
          </div>
        </section>

        <section className="shell section" id="features">
          <div className="eyebrow">KEY FEATURES</div>
          <h2>Everything you need to build and scale AI agents</h2>
          <div className="featureGrid">
            {features.map(([icon, title, text]) => (
              <article key={title}>
                <div className="icon">{icon}</div>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="shell section" id="solutions">
          <div className="eyebrow">USE CASES</div>
          <h2>AI agents for every organization</h2>
          <div className="caseGrid">
            {useCases.map(([icon, title, text]) => (
              <article key={title}>
                <div className="caseIcon">{icon}</div>
                <h3>{title}</h3>
                <p>{text}</p>
                <a href="/signup">Learn more →</a>
              </article>
            ))}
          </div>
        </section>

        <section className="shell section" id="how">
          <div className="eyebrow">HOW IT WORKS</div>
          <h2>Get started in four simple steps</h2>
          <div className="steps">
            <div>
              <b>1</b>
              <span>▤</span>
              <h3>Create</h3>
              <p>Design agents from templates or from scratch.</p>
            </div>
            <div>
              <b>2</b>
              <span>⌘</span>
              <h3>Connect</h3>
              <p>Link your data, tools and integrations.</p>
            </div>
            <div>
              <b>3</b>
              <span>▷</span>
              <h3>Deploy</h3>
              <p>Launch agents to your channels.</p>
            </div>
            <div>
              <b>4</b>
              <span>▥</span>
              <h3>Improve</h3>
              <p>Monitor, evaluate and continuously optimize.</p>
            </div>
          </div>
        </section>

        <section className="shell section">
          <div className="metricPanel">
            <div>
              <div className="eyebrow">BUILT TO OPERATE WITH CONFIDENCE</div>
              <h2>Observe every agent. Improve every workflow.</h2>
              <p>
                Use traces, evaluations and operational analytics to understand what your AI
                workforce is doing and where it can improve.
              </p>
            </div>
            <div className="metrics">
              <div>
                <b>10K+</b>
                <span>Agent runs</span>
              </div>
              <div>
                <b>200+</b>
                <span>Workflows</span>
              </div>
              <div>
                <b>4.9/5</b>
                <span>Quality score</span>
              </div>
              <div>
                <b>99.9%</b>
                <span>Platform uptime</span>
              </div>
            </div>
          </div>
        </section>

        <section className="shell cta">
          <div>
            <div className="eyebrow light">READY TO BUILD YOUR AI WORKFORCE?</div>
            <h2>Turn your ideas into intelligent action.</h2>
            <p>Build AI agents around your organization&apos;s knowledge, workflows and tools.</p>
          </div>
          <div>
            <a className="button white" href="/signup">
              Get started →
            </a>
            <a className="outline" href="mailto:hello@agentforge.ai">
              Contact us
            </a>
          </div>
        </section>
      </main>

      <footer className="shell footer">
        <div>
          <img src="/brand/agentforge-logo.svg" alt="AgentForge" />
          <p>Empowering organizations to build smarter teams with AI.</p>
        </div>
        <div>
          <b>Product</b>
          <a href="#features">Features</a>
          <a href="#platform">Platform</a>
          <a href="#solutions">Solutions</a>
        </div>
        <div>
          <b>Company</b>
          <a href="#top">About</a>
          <a href="mailto:hello@agentforge.ai">Contact</a>
          <a href="#top">Privacy</a>
        </div>
        <div>
          <b>Get started</b>
          <a href="/signin">Sign in</a>
          <a href="/signup">Create account</a>
          <small>© 2026 AgentForge.</small>
        </div>
      </footer>
    </div>
  );
}
