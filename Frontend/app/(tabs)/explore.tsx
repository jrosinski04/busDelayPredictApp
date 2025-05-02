import { StyleSheet, Image, Platform, View, Text } from 'react-native';

import { Collapsible } from '@/components/Collapsible';
import { ExternalLink } from '@/components/ExternalLink';
import ParallaxScrollView from '@/components/ParallaxScrollView';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';
import { IconSymbol } from '@/components/ui/IconSymbol';

export default function TabTwoScreen() {
  return (
    <View style={styles.helpPageContent}>
      <Text style={styles.title}>Help</Text>
      <Text>No one will help you :)</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  helpPageContent: {
    margin: 20,
    marginTop: 60,
  },
  title: {
    fontSize: 20,
    fontWeight: "bold",
    alignSelf: "center",
    marginBottom: 25,
  }
});
