import { Link } from "react-router-dom";

type PublicPageSection = {
  title: string;
  body: string[];
};

type PublicInfoPageProps = {
  eyebrow: string;
  title: string;
  summary: string;
  status?: string;
  sections: PublicPageSection[];
};

const contactGuidance = [
  "Please do not send full manuscripts, full chapters, full AI responses, generated exports unless explicitly requested, passwords, API keys, provider keys, session tokens, private URLs, screenshots containing private story text, or machine-local paths.",
  "Helpful reports usually include your account email, project name or project ID, a short issue summary, an error code if shown, approximate time of the issue, and redacted screenshots.",
];

function PublicInfoPage({ eyebrow, title, summary, status, sections }: PublicInfoPageProps) {
  return (
    <main className="public-page">
      <header className="public-topbar">
        <Link to="/login" className="brand" aria-label="Aevryn login">
          <span className="brand-mark">A</span>
          <span>
            <strong>Aevryn</strong>
            <small>Evidence in. Canon out.</small>
          </span>
        </Link>
        <nav className="public-nav" aria-label="Public pages">
          <Link to="/trust">Trust</Link>
          <Link to="/support">Support</Link>
          <Link to="/privacy">Privacy</Link>
          <Link to="/login">Log in</Link>
        </nav>
      </header>
      <section className="public-hero">
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p>{summary}</p>
        {status ? <p className="public-status">{status}</p> : null}
      </section>
      <section className="public-content" aria-label={`${title} details`}>
        {sections.map((section) => (
          <article className="public-card" key={section.title}>
            <h2>{section.title}</h2>
            {section.body.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </article>
        ))}
      </section>
      <footer className="public-footer">
        <Link to="/terms">Terms</Link>
        <Link to="/acceptable-use">Acceptable Use</Link>
        <Link to="/security/disclosure">Security Disclosure</Link>
      </footer>
    </main>
  );
}

export function TrustPage() {
  return (
    <PublicInfoPage
      eyebrow="Trust"
      title="Your work belongs to you."
      summary="Aevryn is built to understand stories, not to own them."
      status="Public beta is not approved yet. These pages describe the current trust posture and remaining publication boundaries."
      sections={[
        {
          title: "Evidence-backed Canon",
          body: [
            "Aevryn treats your story as the source of truth. Canon facts must be backed by evidence from the story.",
            "If Aevryn cannot support a claim from the source, the right answer is uncertainty, not invention.",
          ],
        },
        {
          title: "AI Never Owns Truth",
          body: [
            "AI can help propose structure. AI does not own truth. Your story wins.",
            "Generated canon, continuity data, prompt packs, and exports remain yours.",
          ],
        },
        {
          title: "Private By Default",
          body: [
            "Aetherra Labs does not train on user stories without explicit opt-in.",
            "Diagnostics and support workflows should investigate problems without requesting full source prose by default.",
          ],
        },
      ]}
    />
  );
}

export function PrivacyPage() {
  return (
    <PublicInfoPage
      eyebrow="Privacy"
      title="Your stories are private by default."
      summary="Aevryn uses uploaded stories to inspect, import, process, display, and export project data for your account."
      status="Draft for attorney review before public launch."
      sections={[
        {
          title: "Story Ownership",
          body: [
            "Uploaded stories belong to their creators.",
            "Aetherra Labs does not train on uploaded stories without explicit opt-in.",
          ],
        },
        {
          title: "Logging Boundaries",
          body: [
            "Aevryn is designed to avoid putting full manuscripts, full chapters, full AI responses, credentials, tokens, private URLs, or machine-local paths into logs, monitoring, diagnostics, or support workflows.",
          ],
        },
        {
          title: "Deletion And Backups",
          body: [
            "Deletion removes active Aevryn-owned project and story storage.",
            "Production backups may retain deleted data for a disclosed recovery window. That window must be published before public beta.",
          ],
        },
        {
          title: "Contact",
          body: ["Privacy questions should go to privacy@aevryn.ai.", ...contactGuidance],
        },
      ]}
    />
  );
}

export function SecurityPage() {
  return (
    <PublicInfoPage
      eyebrow="Security"
      title="Security is architecture, not a feature."
      summary="Aevryn protects user projects through authentication, authorization, private storage boundaries, metadata-only monitoring, security scanning, dependency review, and fail-closed production configuration."
      status="Production security operations and incident-response review remain public-beta blockers."
      sections={[
        {
          title: "Authorization Boundary",
          body: [
            "The website does not grant authority by itself.",
            "Backend authorization decides which projects, stories, imports, snapshots, and exports an account can access.",
          ],
        },
        {
          title: "Private Storage",
          body: [
            "Uploaded manuscripts and generated exports must remain private.",
            "Frontend code never receives object-storage credentials.",
          ],
        },
        {
          title: "Security Reports",
          body: ["Security vulnerability reports should go to security@aevryn.ai.", ...contactGuidance],
        },
      ]}
    />
  );
}

export function UserRightsPage() {
  return (
    <PublicInfoPage
      eyebrow="User Rights"
      title="Aevryn is a tool for understanding your work."
      summary="It is not a claim over your work."
      sections={[
        {
          title: "You Own It",
          body: [
            "Your story: you own it.",
            "Your canon: you own it.",
            "Your exports: you own them.",
          ],
        },
        {
          title: "AI Training",
          body: [
            "AI training is off by default.",
            "Aetherra Labs does not train on user stories without explicit opt-in.",
          ],
        },
        {
          title: "Access",
          body: [
            "Employees do not browse customer stories by default.",
            "Access must be limited, justified, and auditable where technically possible.",
          ],
        },
      ]}
    />
  );
}

export function ContentClassificationPage() {
  return (
    <PublicInfoPage
      eyebrow="Content"
      title="Aevryn is content-aware, not content-opinionated."
      summary="Creators work across many genres, audiences, and formats."
      status="Legal and provider-policy review are required before public beta."
      sections={[
        {
          title: "Ratings",
          body: [
            "Aevryn may classify projects as General, Teen, Mature, or Explicit so the product can handle visibility, provider restrictions, exports, and future moderation responsibly.",
          ],
        },
        {
          title: "Mature Fiction",
          body: [
            "Lawful mature fiction is not automatically prohibited.",
            "Content classification does not change ownership. Your stories remain yours.",
          ],
        },
      ]}
    />
  );
}

export function SupportPage() {
  return (
    <PublicInfoPage
      eyebrow="Support"
      title="Need help with Aevryn?"
      summary="Use the product contact paths below so support can help without exposing private manuscripts by default."
      sections={[
        {
          title: "Product Support",
          body: [
            "Use support@aevryn.ai for product support, account access help, import or processing issues, export issues, and project deletion help.",
          ],
        },
        {
          title: "Privacy And Security",
          body: [
            "Use privacy@aevryn.ai for privacy questions, account deletion requests, backup retention questions, or AI provider data-use questions.",
            "Use security@aevryn.ai for vulnerability reports, suspected account compromise, or suspected data exposure.",
          ],
        },
        {
          title: "Abuse Reports",
          body: [
            "Use abuse@aevryn.ai for platform abuse, spam, malware, illegal use reports, copyright or rights escalations, or attempts to access another user's data.",
          ],
        },
        {
          title: "What To Include",
          body: contactGuidance,
        },
      ]}
    />
  );
}

export function SecurityDisclosurePage() {
  return (
    <PublicInfoPage
      eyebrow="Security Disclosure"
      title="Report vulnerabilities privately."
      summary="Aetherra Labs welcomes good-faith security reports for Aevryn."
      status="Attorney safe-harbor review remains required before public launch."
      sections={[
        {
          title: "Where To Report",
          body: ["Please report suspected vulnerabilities privately to security@aevryn.ai."],
        },
        {
          title: "What To Include",
          body: [
            "Reports should include the affected component, reproduction steps, impact, screenshots or logs without private story content, and suggested remediation if available.",
          ],
        },
        {
          title: "Research Boundaries",
          body: [
            "Please avoid accessing another user's data, altering or deleting data, exfiltrating secrets, degrading service availability, social engineering, physical attacks, or public disclosure before remediation coordination.",
            "No vulnerability report should require private user manuscripts.",
          ],
        },
      ]}
    />
  );
}

export function TermsPage() {
  return (
    <PublicInfoPage
      eyebrow="Terms"
      title="Aevryn Terms of Service"
      summary="These draft terms describe intended product boundaries for Aevryn."
      status="Draft for attorney review before public launch."
      sections={[
        {
          title: "User Responsibilities",
          body: [
            "Users are responsible for their accounts, uploaded content, and lawful use of Aevryn.",
            "Aetherra Labs may suspend or terminate accounts that violate terms or create security risk.",
          ],
        },
        {
          title: "Intellectual Property",
          body: [
            "Users retain ownership of uploaded stories and generated project outputs.",
            "Aetherra Labs does not claim ownership of user manuscripts through product use.",
          ],
        },
        {
          title: "Legal Review",
          body: [
            "Payments, warranties, liability limits, and governing law must be finalized by counsel before public launch.",
          ],
        },
      ]}
    />
  );
}

export function AcceptableUsePage() {
  return (
    <PublicInfoPage
      eyebrow="Acceptable Use"
      title="Use Aevryn responsibly."
      summary="Aevryn supports creative and analytical story work while protecting users and the platform."
      status="Draft for attorney review before public launch."
      sections={[
        {
          title: "Allowed Uses",
          body: ["Fiction, screenplays, comics, mature novels, and academic work are expected uses."],
        },
        {
          title: "Not Allowed",
          body: [
            "Do not use Aevryn for copyright infringement, malware, spam, illegal material, or attempts to attack the platform.",
          ],
        },
        {
          title: "Enforcement",
          body: [
            "Aetherra Labs may limit, suspend, or terminate access for violations, security risk, legal obligations, or platform abuse.",
          ],
        },
      ]}
    />
  );
}
