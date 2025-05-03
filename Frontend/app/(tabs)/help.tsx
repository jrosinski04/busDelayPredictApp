import { StyleSheet, Image, Platform, View, Text, ScrollView } from 'react-native';

export default function HelpPage() {
  return (
    <ScrollView contentContainerStyle={styles.helpPageContent}>
      <Text style={styles.title}>Help & About</Text>

      <Text style={styles.sectionTitle}>What This App Does</Text>
      <Text style={styles.paragraph}>
        This app predicts delays on Bee Network bus services. You choose the bus, stop, direction,
        date and time. The app will then provide an estimate of whether that bus is expected to be
        on time or delayed, based on previous journeys.
      </Text>

      <Text style={styles.sectionTitle}>How It Works</Text>
      <Text style={styles.paragraph}>
        The app uses a machine learning model called LightGBM to estimate delays. The model was trained
        on historical data including:
      </Text>
      <Text style={styles.bullet}>• Scheduled and actual departure times</Text>
      <Text style={styles.bullet}>• Day of the week and whether it’s during peak hours</Text>
      <Text style={styles.bullet}>• The location of your stop on the route</Text>
      <Text style={styles.bullet}>• Start and end points of the service</Text>
      <Text style={styles.paragraph}>
        When you enter a time and stop, the app finds similar past journeys and uses that data to
        estimate delay in minutes.
      </Text>

      <Text style={styles.sectionTitle}>Transparency & Your Rights</Text>
      <Text style={styles.paragraph}>
        In line with UK guidance on AI transparency, the user should be informed about the basics of how this
        system works. No personal data is used. All delay estimates are statistical guesses based
        on historical patterns — they are not guaranteed predictions.
      </Text>
      <Text style={styles.paragraph}>
        If you’d like more technical details or have questions about how the model was trained, feel
        free to contact us at BusDelayPredict@protonmail.com.
      </Text>

      <Text style={styles.sectionTitle}>📌 Disclaimer</Text>
      <Text style={styles.paragraph}>
        This app provides AI-generated delay estimates based on historical data. It cannot predict
        accidents, road closures, or real-time incidents. Please use your own judgment when making
        travel decisions.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  helpPageContent: {
    padding: 20,
    paddingTop: 60,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    alignSelf: 'center',
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginTop: 20,
    marginBottom: 8,
  },
  paragraph: {
    fontSize: 16,
    lineHeight: 22,
    marginBottom: 12,
  },
  bullet: {
    fontSize: 16,
    lineHeight: 22,
    marginLeft: 12,
  },
});
