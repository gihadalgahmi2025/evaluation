
			<p>A target was raised to <b>Critical</b> priority.</p>
			<ul>
				<li>Target: <a href="/app/target/{{ doc.name }}">{{ doc.target_name }}</a></li>
				<li>Type: {{ doc.target_type or "-" }}</li>
				<li>Unit: {{ doc.evaluation_unit }}</li>
				<li>Confidence: {{ doc.confidence or "-" }}</li>
			</ul>
		