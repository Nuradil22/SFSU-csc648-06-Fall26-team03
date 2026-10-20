-- CareerGPS database schema (PostgreSQL / Supabase).
-- Generated from app/models.py; the app creates these tables on startup,
-- so this file is reference documentation, not something you need to run.

CREATE TABLE users (
	id SERIAL NOT NULL,
	name VARCHAR NOT NULL,
	email VARCHAR NOT NULL,
	hashed_password VARCHAR NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE INDEX ix_users_id ON users (id);

CREATE TABLE portfolios (
	id SERIAL NOT NULL,
	user_id INTEGER NOT NULL,
	headline VARCHAR(200),
	bio TEXT,
	location VARCHAR(200),
	profile_image_url VARCHAR(1000),
	career_interests JSONB NOT NULL,
	is_public BOOLEAN NOT NULL,
	share_token VARCHAR(64),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_portfolios_share_token ON portfolios (share_token);
CREATE UNIQUE INDEX ix_portfolios_user_id ON portfolios (user_id);

CREATE TABLE career_guidance (
	id SERIAL NOT NULL,
	portfolio_id INTEGER NOT NULL,
	summary TEXT NOT NULL,
	career_paths JSONB NOT NULL,
	strengths JSONB NOT NULL,
	improvements JSONB NOT NULL,
	next_steps JSONB NOT NULL,
	provider VARCHAR(50) NOT NULL,
	model VARCHAR(100),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(portfolio_id) REFERENCES portfolios (id) ON DELETE CASCADE
);

CREATE INDEX ix_career_guidance_portfolio_id ON career_guidance (portfolio_id);

CREATE TABLE education (
	id SERIAL NOT NULL,
	portfolio_id INTEGER NOT NULL,
	school_name VARCHAR(200) NOT NULL,
	degree VARCHAR(200),
	major VARCHAR(200),
	start_date DATE,
	graduation_date DATE,
	gpa VARCHAR(20),
	coursework JSONB NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(portfolio_id) REFERENCES portfolios (id) ON DELETE CASCADE
);

CREATE INDEX ix_education_portfolio_id ON education (portfolio_id);

CREATE TABLE experiences (
	id SERIAL NOT NULL,
	portfolio_id INTEGER NOT NULL,
	experience_type VARCHAR(30) NOT NULL,
	organization VARCHAR(200) NOT NULL,
	position VARCHAR(200) NOT NULL,
	location VARCHAR(200),
	start_date DATE,
	end_date DATE,
	is_current BOOLEAN NOT NULL,
	description TEXT,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(portfolio_id) REFERENCES portfolios (id) ON DELETE CASCADE
);

CREATE INDEX ix_experiences_portfolio_id ON experiences (portfolio_id);

CREATE TABLE portfolio_links (
	id SERIAL NOT NULL,
	portfolio_id INTEGER NOT NULL,
	label VARCHAR(100) NOT NULL,
	url VARCHAR(1000) NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(portfolio_id) REFERENCES portfolios (id) ON DELETE CASCADE
);

CREATE INDEX ix_portfolio_links_portfolio_id ON portfolio_links (portfolio_id);

CREATE TABLE projects (
	id SERIAL NOT NULL,
	portfolio_id INTEGER NOT NULL,
	title VARCHAR(200) NOT NULL,
	description TEXT NOT NULL,
	content_blocks JSONB NOT NULL,
	project_date VARCHAR(100),
	subject VARCHAR(200),
	technologies JSONB NOT NULL,
	display_order INTEGER NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(portfolio_id) REFERENCES portfolios (id) ON DELETE CASCADE
);

CREATE INDEX ix_projects_portfolio_id ON projects (portfolio_id);

CREATE TABLE skills (
	id SERIAL NOT NULL,
	portfolio_id INTEGER NOT NULL,
	name VARCHAR(100) NOT NULL,
	category VARCHAR(30) NOT NULL,
	proficiency VARCHAR(30),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(portfolio_id) REFERENCES portfolios (id) ON DELETE CASCADE
);

CREATE INDEX ix_skills_portfolio_id ON skills (portfolio_id);

CREATE TABLE project_media (
	id SERIAL NOT NULL,
	project_id INTEGER NOT NULL,
	media_type VARCHAR(20) NOT NULL,
	url VARCHAR(1000) NOT NULL,
	label VARCHAR(200),
	link_type VARCHAR(30),
	storage_path VARCHAR(500),
	display_order INTEGER NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
);

CREATE INDEX ix_project_media_project_id ON project_media (project_id);

CREATE TABLE project_models (
	id SERIAL NOT NULL,
	project_id INTEGER NOT NULL,
	url VARCHAR(1000) NOT NULL,
	file_format VARCHAR(10) NOT NULL,
	original_filename VARCHAR(255),
	file_size_bytes INTEGER,
	storage_path VARCHAR(500),
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_project_models_project_id ON project_models (project_id);

